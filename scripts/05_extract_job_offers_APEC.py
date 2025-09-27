from src.ai_scrapper_jobmarket.apec import (
    add_url,
    apply_mapping_recursive,
    get_data,
    validate_and_save_as_json,
)

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

base_url = "https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/{id}W?motsCles=data%20scientist&salaireMinimum=20&salaireMaximum=200&typesContrat=101887&typesConvention=143684&typesConvention=143685&typesConvention=143686&typesConvention=143687&typesConvention=143706&selectedIndex=1&page=0"

save_path = "data/processed/json/APEC_offers.json"


def main():
    raw_data = get_data(
        url=url,
        cURL_request_data=cURL_request_data,
        page_index=page_index,
        headers=headers,
    )
    updated_data = add_url(raw_data, base_url)
    transformed_data = apply_mapping_recursive(updated_data, code_mapping)
    success = validate_and_save_as_json(transformed_data, save_path)
    if success:
        print("Job's done")
    else:
        print("data not valid")


if __name__ == "__main__":
    main()
