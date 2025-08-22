import os
import platform
import subprocess

# Installer path (change this to your real installer .exe or .msi)
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
        if not os.path.exists(LINUX_TARBALL):
            return f"Installer not found at {LINUX_TARBALL}"

        extracted_dir = os.path.join(BASE_DIR, "ai_agent-linux")

        try:
            # 1. Extract tarball
            subprocess.run(f"tar -zxf {LINUX_TARBALL}", shell=True, check=True)

            # 2. Run installer script with passwordless sudo
            install_script = os.path.join(extracted_dir, "x64", "ai-agent-install.sh")
            subprocess.run(f"sudo {install_script}", shell=True, check=True)

            # 3. Cleanup
            subprocess.run(f"rm -rf {extracted_dir}", shell=True, check=True)

            return "Installer ran successfully (Linux tarball, passwordless)."

        except subprocess.CalledProcessError as e:
            return f"Linux installer error: {e}
