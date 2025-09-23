import json
from pathlib import Path

import requests
from pydantic import ValidationError

from src.ai_scrapper_jobmarket.models import JobSearchResponse


def get_data(url: str, cURL_request_data: dict, page_index: int, headers: dict) -> dict:
    """query the hidden API for a specific page"""
    cURL_request_data["pagination"]["startIndex"] = page_index  # update the page index
    post_response = requests.post(url, headers, json=cURL_request_data)
    post_response.raise_for_status()
    raw_data = post_response.json()
    return raw_data


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
