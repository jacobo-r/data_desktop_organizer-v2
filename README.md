To deploy: download exec and JSON from dist folder, create a receiver_folder in path stated in config JSON

Crear ejecutable y distribuir

pyinstaller --onefile --noconsole --add-data "config.json;." run.py
