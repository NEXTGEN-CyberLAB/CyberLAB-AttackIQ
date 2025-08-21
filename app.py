from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import platform
import subprocess
import winreg
import os
from aiq_api import load_config, run_local

app = Flask(__name__)

# Installer path (change this to your real installer .exe or .msi)
INSTALLER_PATH = r"C:\path\to\installer.exe"

def get_machine_id():

    system = platform.system()

    if system == "Windows":
        try:
            key_path = r"SOFTWARE\AiPersist"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuidV2")
                return value
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Registry check error: {e}")
            return None

    elif system == "Linux":
        file_path = "/opt/attackiq/agent-data/idv2"
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"File read error: {e}")
                return None
        return None

    else:
        print(f"Unsupported OS: {system}")
        return None

def run_installer():
    if os.path.exists(INSTALLER_PATH):
        try:
            subprocess.Popen([INSTALLER_PATH], shell=True)
            return True
        except Exception as e:
            return str(e)
    else:
        return "Installer not found at path"

        
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
