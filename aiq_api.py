

import requests
import os
import json
from requests.exceptions import HTTPError
from helper import get_machine_id, get_token

computer_name = os.environ['COMPUTERNAME']

base_url = "https://nextgen-cyberlab.attackiq.com.au/v1/"
private_token = get_token()

guid = get_machine_id()
CONFIG_FILE = "config.json"

# Load config.json
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"attackiq": {}}

# Save config.json
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# Create an assessment
def create_assessment(uuid,guid):
    assessment_name = guid[:6]
    url = f"{base_url}assessments/project_from_template"
    headers = {
        "Authorization": f"Token {private_token}",
        "Content-Type": "application/json"
    }


    payload = {
        "project_name": f"{assessment_name}",
        "template": f"{uuid}"
    } 
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    # Check the response
    print("Status code:", response.status_code)
    print("Response text:", response.text)
    

    return data.get('project_id')

# Attach an machine to the assessment
def add_asset(aid, guid):
    url = f"{base_url}assessments/{aid}/update_defaults"
    headers = {
        "Authorization": f"Token {private_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "assets":f'{guid}'
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    # Check the response
    print("Status code:", response.status_code)

# Start the assesment
def start_assessment(aid):
    url = f"{base_url}assessments/{aid}/run_all"

    headers = {
        "Authorization": f"Token {private_token}",
        "Content-Type": "application/json"
    }


    payload = {} 
    response = requests.post(url, headers=headers, json=payload)


def run_local(asset_id, attack_name):
    config = load_config()
    attacks = config.setdefault("attackiq", {})

    if attack_name not in attacks:
        raise ValueError(f"Attack '{attack_name}' not found in config!")

    attack_config = attacks[attack_name]
    template_id = attack_config.get("template_id")
    assessment_id = attack_config.get("assessment_id")

    if not template_id:
        raise ValueError(f"Template ID not set for attack '{attack_name}'")

    def ensure_assessment(current_id):
        """Returns a valid assessment ID"""
        if not current_id:
            new_id = create_assessment(template_id, asset_id)
            print(f"Created new assessment for '{attack_name}': {new_id}")
            attack_config["assessment_id"] = new_id
            save_config(config)

            return new_id
        else:
            return current_id

    assessment_id = ensure_assessment(assessment_id)

    try:
        add_asset(assessment_id, asset_id)
        result = start_assessment(assessment_id)
        # return result
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"Assessment {assessment_id} is invalid or deleted. Creating new assessment...")
            assessment_id = ensure_assessment(None)
            add_asset(assessment_id, asset_id)
            result = start_assessment(assessment_id)
            # return result
        else:
            raise
    



