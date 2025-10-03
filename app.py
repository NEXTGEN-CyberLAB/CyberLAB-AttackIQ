from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import platform
import os
import sys
import json

from aiq_api import load_config, run_local
from helper import get_machine_id, run_installer_windows, run_installer_linux
from runtime_config import RES_DIR, CONFIG_PATH

app = Flask(
    __name__,
    template_folder=os.path.join(RES_DIR, "templates"),
    static_folder=os.path.join(RES_DIR, "static"),
)

app.secret_key = os.environ.get("SECRET_KEY", "dev")

def load_config():
    cfg = {}
    print(os.path.exists(CONFIG_PATH))
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            cfg = {}
    cfg.setdefault("attackiq", {})
    # prefer env for secret
    cfg["aiq_token"] = os.environ.get("AIQ_TOKEN", cfg.get("aiq_token"))
    return cfg

# ----------------------------
# Helpers
# ----------------------------
def is_agent_installed() -> bool:
    """We treat 'has machine id' as proxy for installed agent."""
    try:
        return bool(get_machine_id())
    except Exception:
        return False


def run_installer():
    """Choose the platform-appropriate installer."""
    try:
        system = platform.system().lower()
        if "windows" in system:
            return run_installer_windows()
        return run_installer_linux()
    except Exception as e:
        raise RuntimeError(f"Installer failed: {e}")


def host_metadata():
    """Collect light host metadata for status page (optional)."""
    try:
        return {
            "hostname": platform.node(),
            "os_name": f"{platform.system()} {platform.release()}",
            "asset_id": get_machine_id() or None,
            "agent_version": None,  
            "tenant": None,         
            "last_seen": None,      
        }
    except Exception:
        return {}


def service_checks(agent_ok: bool):
    """
    Minimal example 'services' list for the table.
    Add more checks (e.g., process presence, network reachability) as needed.
    """
    return [
        {
            "name": "AttackIQ Agent",
            "ok": agent_ok,
            "detail": "Detected" if agent_ok else "Not detected",
        }
    ]


# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def home_redirect():
    # Send homepage to the Attacks launcher
    return redirect(url_for("attacks"))


@app.route("/attacks")
def attacks():
    """Launcher grid (index.html)."""
    cfg = load_config()
    attacks_dict = cfg.get("attackiq", {}) if isinstance(cfg, dict) else {}
    return render_template("index.html", attacks=attacks_dict)


@app.route("/status")
def status():
    """Status page to check if the AttackIQ agent is installed."""
    agent_installed = is_agent_installed()
    meta = host_metadata()

    # Build services list (or set to [] to hide the Services card)
    services = service_checks(agent_installed)

    # Render — note we pass keys used by the template (with safe defaults)
    return render_template(
        "status.html",
        agent_installed=agent_installed,
        hostname=meta.get("hostname"),
        os_name=meta.get("os_name"),
        asset_id=meta.get("asset_id"),
        agent_version=meta.get("agent_version"),
        tenant=meta.get("tenant"),
        last_seen=meta.get("last_seen"),
        services=services,  
    )


@app.route("/status/install", methods=["POST", "GET"])
def status_install():
    """One-click Install/Repair action (optional)."""
    try:
        run_installer()
        flash("Installer executed. Re-checking status…", "success")
    except Exception as e:
        flash(f"Installer error: {e}", "error")
    return redirect(url_for("status"))


@app.route("/run/<attack_name>")
def run_attack(attack_name):
    """Start a local attack from config."""
    cfg = load_config()
    attacks_dict = cfg.get("attackiq", {}) if isinstance(cfg, dict) else {}
    if attack_name not in attacks_dict:
        flash(f"Attack '{attack_name}' not found in config", "error")
        return redirect(url_for("attacks"))

    asset_id = get_machine_id()
    if not asset_id:
        # Try installer then re-check
        try:
            run_installer()
        except Exception as e:
            flash(f"Agent install failed: {e}", "error")
            return redirect(url_for("status"))
        asset_id = get_machine_id()
        if not asset_id:
            flash("Agent still not detected after install attempt.", "error")
            return redirect(url_for("status"))

    try:
        result = run_local(asset_id, attack_name)
        return render_template("result.html", attack_name=attack_name, result=result)
    except Exception as e:
        return render_template("result.html", attack_name=attack_name, result=f"Error: {e}")


# ----------------------------
# Entrypoint
# ----------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
