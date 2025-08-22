from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import platform
import subprocess
import os
from aiq_api import load_config, run_local
from helper import get_machine_id, run_installer

app = Flask(__name__)

# Installer path (change this to your real installer .exe or .msi)
INSTALLER_PATH = r"C:\path\to\installer.exe"




@app.route("/")
def index():
    return redirect(url_for("status"))

# Status page to check if AttackIQ agent is installed.
@app.route("/status")
def status():
    machine_id = get_machine_id()
    return render_template("status.html", machine_id=machine_id)


# Run the installer
@app.route("/install")
def install_agent():
    result = run_installer()
    return f"Installer launched: {result}"

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
