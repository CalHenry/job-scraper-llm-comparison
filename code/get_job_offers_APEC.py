import json
from pathlib import Path
from typing import List, Optional

import requests
from pydantic import BaseModel, Field, ValidationError


# pydantic models of the response
class ApecJobOffer(BaseModel):
    "model for a single job offer"

    id: int
    intitule: str
    lieuTexte: str
    salaireTexte: Optional[str]
    texteOffre: str
    datePublication: Optional[str]
    typeContrat: Optional[str]
    contractDuration: Optional[int]
    url: str


class JobSearchResponse(BaseModel):
    "main model for the API response"

    resultats: List[ApecJobOffer] = Field(description="job offer content")
    totalCount: Optional[int] = Field(description="number of offers found")


# to translate the job type code
code_mapping = {
    101888: "CDI",
    101887: "CDD",
}

# API request element from cURL command
url = "https://www.apec.fr/cms/webservices/rechercheOffre"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Content-Type": "application/json",
}

cURL_request_data = {
    "motsCles": "data scientist",
    "typesConvention": ["143684", "143685", "143686", "143687", "143706"],
    "typeClient": "CADRE",
    "sorts": [{"type": "DATE", "direction": "DESCENDING"}],  # sort by date
    "pagination": {"range": 20, "startIndex": 0},  # 20 offer per pages, page 0
    "lieux": [],
    "fonctions": [],
    "statutPoste": [],
    "typesContrat": ["101888", "101887"],  # CDI and CDD
    "niveauxExperience": [],
    "idsEtablissement": [],
    "secteursActivite": [],
    "typesTeletravail": [],
    "idNomZonesDeplacement": [],
    "positionNumbersExcluded": [],
    "activeFiltre": True,
    "pointGeolocDeReference": {"distance": 0},
}

page_index = 0


def get_data(url: str, cURL_request_data: dict, page_index: int = page_index) -> dict:
    """query the hidden API for a specific page"""
    cURL_request_data["pagination"]["startIndex"] = page_index  # update the page index
    post_response = requests.post(url, json=cURL_request_data, headers=headers)
    post_response.raise_for_status()
    raw_data = post_response.json()
    return raw_data


base_url = "https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/{id}W?motsCles=data%20scientist&salaireMinimum=20&salaireMaximum=200&typesContrat=101887&typesConvention=143684&typesConvention=143685&typesConvention=143686&typesConvention=143687&typesConvention=143706&selectedIndex=1&page=0"


def add_url(raw_data, base_url) -> dict:
    for item in raw_data["resultats"]:
        item["url"] = base_url.format(id=item["id"])
    return raw_data


def apply_mapping_recursive(data, value_mapping) -> dict:
    """Recursively replace values in nested dictionary/list structure"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                result[key] = apply_mapping_recursive(value, value_mapping)
            else:
                result[key] = value_mapping.get(value, value)
        return result
    elif isinstance(data, list):
        return [apply_mapping_recursive(item, value_mapping) for item in data]
    else:
        return value_mapping.get(data, data)


save_path = "outputs/json_files/APEC_offers.json"


def validate_and_save_as_json(updated_dict: dict, save_path: str) -> dict:
    """validate the model on the data and save to a JSON file"""
    try:
        response = JobSearchResponse(**updated_dict)

        save_path_obj = Path(save_path)

        # merge with existing file, removes duplicates
        if save_path_obj.exists():
            with open(save_path_obj, "r") as file:
                existing_data = json.load(file)

            existing_response = JobSearchResponse(**existing_data)
            combined_jobs = existing_response.jobs + response.jobs

            # Remove duplicates based on 'id'
            seen_refs = set()
            unique_jobs = []
            for job in combined_jobs:
                if job.ref not in seen_refs:
                    unique_jobs.append(job)
                    seen_refs.add(job.id)

            response.jobs = unique_jobs

        data_json = response.model_dump_json(indent=2)

        with open(save_path_obj, "w") as file:
            file.write(data_json)
        return True
    except ValidationError as e:
        print("Validation error:", e)
        return False


def main():
    raw_data = get_data(url=url, cURL_request_data=cURL_request_data)
    updated_data = add_url(raw_data, base_url)
    transformed_data = apply_mapping_recursive(updated_data, code_mapping)
    success = validate_and_save_as_json(transformed_data, save_path)
    if success:
        print("Job's done")
    else:
        print("data not valid")


if __name__ == "__main__":
    main()
