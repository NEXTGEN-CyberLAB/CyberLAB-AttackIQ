import os
import platform
import subprocess

INSTALLER_PATH = 'AttackIQAgent-installer-sfx.exe'
LINUX_TARBALL =  "ai_agent-linux-amd64-3.9.75.tar.gz"

if platform.system() == "Windows":
    import winreg

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

def run_installer_windows():

    system = platform.system()

    if os.path.exists(INSTALLER_PATH):
        try:
            subprocess.Popen([INSTALLER_PATH], shell=True)
            return True
        except Exception as e:
            return str(e)
    else:
        return "Installer not found at path"

    

def run_installer_linux(password):
    try:
        subprocess.run("tar -zxf ai_agent-linux-amd64-3.9.75.tar.gz", shell=True, check=True)
        subprocess.run(
            ["sudo", "-S", "./ai_agent-linux/x64/ai-agent-install.sh"],
            input=f"{password}\n",
            text=True,
            check=True
        )
        subprocess.run("rm -rf ./ai_agent-linux", shell=True, check=True)
        return "Linux installer ran successfully."
    except subprocess.CalledProcessError as e:
        return f"Linux installer error: {e}"