import winreg
import os
import platform
import subprocess

# Installer path (change this to your real installer .exe or .msi)
INSTALLER_PATH = 'AttackIQAgent-installer-sfx.exe'
LINUX_TARBALL =  "ai_agent-linux-amd64-3.9.75.tar.gz"

def get_token():
    return os.getenv("AiqToken")

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

    system = platform.system()
    if system == 'Windows':
        if os.path.exists(INSTALLER_PATH):
            try:
                subprocess.Popen([INSTALLER_PATH], shell=True)
                return True
            except Exception as e:
                return str(e)
        else:
            return "Installer not found at path"

    elif system == "Linux":
        if os.path.exists(LINUX_TARBALL):
            cmd = (
                f"sudo bash -c "
                f"\"tar -zxf {LINUX_TARBALL} "
                f"&& ./ai_agent-linux/x64/ai-agent-install.sh "
                f"&& rm -rf ./ai_agent-linux/\""
            )
            try:
                subprocess.run(cmd, shell=True, check=True)
                return "Installer ran successfully (Linux tarball)."
            except subprocess.CalledProcessError as e:
                return f"Linux installer error: {e}"
        else:
            return f"Installer not found at {LINUX_TARBALL}"
