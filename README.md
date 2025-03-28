To deploy: download exec and JSON from dist folder, create a receiver_folder in path stated in config JSON

Crear ejecutable y distribuir

pyinstaller --onefile --noconsole --add-data "config.json;." run.py





def download_file(filename):
    url = f"{GET_FILE_URL}/{filename}?token={TOKEN}"
    file_path = os.path.join(DEST_FOLDER, filename)

    print(f"⬇ Downloading {filename}...")

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Saved to {file_path}")

        # Convert if it's .ogg
        if filename.lower().endswith(".ogg"):
            mp3_path = os.path.join(DEST_FOLDER, filename.replace(".ogg", ".mp3"))
            convert_ogg_to_mp3(file_path, mp3_path)
            os.remove(file_path)
            print(f"🗑️ Deleted .ogg: {file_path}")
        elif filename.lower().endswith(".mp4"):
            print(f"📼 File is .mp4, keeping original: {file_path}")
        else:
            print(f"⚠️ Unknown file type: {filename}")

        return True
    except Exception as e:
        print(f"❌ Failed to download or process {filename}: {e}")
        return False
