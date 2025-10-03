import os, sys

if getattr(sys, "frozen", False):
    # EXE case
    APP_DIR = os.path.dirname(sys.executable)  # external files live next to the EXE
    RES_DIR = getattr(sys, "_MEIPASS", APP_DIR)  # bundled resources extracted here
else:
    # Dev case (python app.py)
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RES_DIR = APP_DIR

CONFIG_PATH = os.path.join(APP_DIR, "config.json")