import os
import sys
import json
import time
import requests
from requests.exceptions import HTTPError, RequestException

from helper import get_machine_id, get_token  # you already have these
from runtime_config import CONFIG_PATH
# ---------------------------------------------------------------------
# Base/paths – works for both python and PyInstaller EXE (--onefile)
# ---------------------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# ---------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------
BASE_URL = "https://nextgen-cyberlab.attackiq.com.au/v1/"  # trailing slash ok

# Prefer environment (best for services/EXE), fallback to helper

GUID = get_machine_id()  # machine / asset identifier

# Small HTTP client with timeouts & raise_for_status by default
SESSION = requests.Session()
DEFAULT_TIMEOUT = 30


def _auth_headers() -> dict:
    PRIVATE_TOKEN = os.environ.get("AiqToken") or get_token()
    return {
        "Authorization": f"Token {PRIVATE_TOKEN}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------
def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                cfg = json.load(f)
            except json.JSONDecodeError:
                cfg = {}
    else:
        cfg = {}

    # shape safety
    cfg.setdefault("attackiq", {})
    return cfg


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# ---------------------------------------------------------------------
# AttackIQ API wrappers
# (Endpoints based on your current code; adjust if API differs)
# ---------------------------------------------------------------------
def create_assessment(template_uuid: str, guid: str) -> str:
    """
    Create a project/assessment from a template.
    Returns the new project/assessment id (string).
    """
    # short, unique-ish project name
    assessment_name = f"{guid[:6]}-{int(time.time())}"

    url = f"{BASE_URL}assessments/project_from_template"
    payload = {
        "project_name": f"{assessment_name}",
        "template": f"{template_uuid}",
    }

    resp = SESSION.post(url, headers=_auth_headers(), json=payload, timeout=DEFAULT_TIMEOUT)
    # surface HTTP errors
    try:
        resp.raise_for_status()
    except HTTPError:
        # helpful print for logs
        print("create_assessment error:", resp.status_code, resp.text)
        raise

    data = resp.json() if resp.content else {}
    project_id = data.get("project_id")
    if not project_id:
        raise RuntimeError(f"project_id missing in response: {data}")
    return project_id


def add_asset(assessment_id: str, guid: str) -> None:
    """
    Attach machine to assessment defaults.
    Many APIs expect a LIST for assets – we send [guid].
    """
    url = f"{BASE_URL}assessments/{assessment_id}/update_defaults"
    print(guid)
    payload = {
        "assets": f'{guid}' # IMPORTANT: list not string
    }

    resp = SESSION.post(url, headers=_auth_headers(), json=payload, timeout=DEFAULT_TIMEOUT)
    try:
        resp.raise_for_status()
    except HTTPError:
        print("add_asset error:", resp.status_code, resp.text)
        raise


def start_assessment(assessment_id: str) -> dict:
    """
    Start/run all tests in an assessment.
    Returns JSON response.
    """
    url = f"{BASE_URL}assessments/{assessment_id}/run_all"

    resp = SESSION.post(url, headers=_auth_headers(), json={}, timeout=DEFAULT_TIMEOUT)
    try:
        resp.raise_for_status()
    except HTTPError:
        print("start_assessment error:", resp.status_code, resp.text)
        raise

    return resp.json() if resp.content else {}


# ---------------------------------------------------------------------
# Public entry used by your Flask route
# ---------------------------------------------------------------------
def run_local(asset_id: str, attack_name: str) -> dict:
    """
    - Loads config
    - Ensures an assessment exists (create if missing)
    - Adds the asset
    - Starts the assessment
    - If 403/404 indicates the saved assessment became invalid, create a new one and retry once
    """
    config = load_config()
    attacks = config.setdefault("attackiq", {})

    if attack_name not in attacks:
        raise ValueError(f"Attack '{attack_name}' not found in config!")

    attack_config = attacks[attack_name]
    template_id = attack_config.get("template_id") or attack_config.get("blueprint_id")
    assessment_id = attack_config.get("assessment_id") or ""

    if not template_id:
        raise ValueError(f"Template ID not set for attack '{attack_name}'")

    def ensure_assessment(current_id: str) -> str:
        if not current_id:
            new_id = create_assessment(template_id, asset_id)
            # persist for reuse
            attack_config["assessment_id"] = new_id
            save_config(config)
            return new_id
        return current_id

    # first ensure
    assessment_id = ensure_assessment(assessment_id)

    try:
        add_asset(assessment_id, asset_id)
        return start_assessment(assessment_id)

    except HTTPError as e:
        status = getattr(e.response, "status_code", None)
        # If assessment is invalid or gone, recreate once
        if status in (403, 404):
            print(f"Assessment {assessment_id} invalid (HTTP {status}). Creating new and retrying once...")
            assessment_id = ensure_assessment("")  # force new
            add_asset(assessment_id, asset_id)
            return start_assessment(assessment_id)
        raise

    except RequestException as e:
        # Network-level issues, timeouts, etc.
        print(f"Network error: {e}")
        raise