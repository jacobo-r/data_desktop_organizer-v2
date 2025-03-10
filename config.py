import json
import os
import sys 

# Get the directory where the executable is located
if getattr(sys, 'frozen', False):  # If running as a PyInstaller executable
    BASE_DIR = os.path.dirname(sys.executable)
else:  # If running as a script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    raise FileNotFoundError(f"Configuration file {CONFIG_FILE} not found!")

# Convert paths to raw strings and absolute paths
DESKTOP_DIR = os.path.normpath(config["DESKTOP_DIR"])
RECEIVER_DIR = os.path.normpath(config["RECEIVER_DIR"])
DATABASE_DIR = os.path.normpath(config["DATABASE_DIR"])
AMBULATORIOS_DIR = os.path.normpath(config["AMBULATORIOS_DIR"])

# Print for verification
print(f"DESKTOP_DIR: {DESKTOP_DIR}")
print(f"RECEIVER_DIR: {RECEIVER_DIR}")
print(f"DATABASE_DIR: {DATABASE_DIR}")
print(f"AMBULATORIOS_DIR: {AMBULATORIOS_DIR}")

