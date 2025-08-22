from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import platform
import subprocess
import os
from aiq_api import load_config, run_local
from helper import get_machine_id, run_installer_windows, run_installer_linux

app = Flask(__name__)



@app.route("/")
def index():
    return redirect(url_for("status"))

# Status page to check if AttackIQ agent is installed.
@app.route("/status")
def status():
    machine_id = get_machine_id()
    agent_installed = bool(machine_id)
    system = platform.system()
    return render_template("status.html", machine_id=machine_id, agent_installed=agent_installed,system = system)


# Run the installer
@app.route("/install", methods=["POST"])
def install_agent():
    system = platform.system()
    
    if system == "Linux":
        password = request.form.get("password")
        if not password:
            return "Password required."
        result = run_installer_linux(password)
    else:
        result = run_installer_windows()  # Windows EXE

    # Check if agent exists now
    machine_id = get_machine_id()
    if machine_id:
        return redirect(url_for("attacks_page"))
    else:
        return render_template("status.html", machine_id=None, agent_installed=False, install_result=result)

# Attack page
@app.route("/attacks")
def attacks_page():

    machine_id = get_machine_id()
    if not machine_id:
        return redirect(url_for("status"))
    config = load_config()
    attacks = config.get("attackiq", {})
    return render_template("index.html", attacks=attacks)

# Run the attack 
@app.route("/run/<attack_name>")
def run_attack(attack_name):
    config = load_config()
    attacks = config.get("attackiq", {})
    if attack_name not in attacks:
        flash(f"Attack '{attack_name}' not found in config", "error")
        return redirect(url_for("index"))

    asset_id = get_machine_id()
    if not asset_id:
        run_installer()
    try:
        result = run_local(asset_id, attack_name)
        return render_template("result.html", attack_name=attack_name, result=result)
    except Exception as e:
        return render_template("result.html", attack_name=attack_name, result=f"Error: {e}")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
