To deploy: download exec and JSON from dist folder, create a receiver_folder in path stated in config JSON

Crear ejecutable y distribuir

pyinstaller --onefile --noconsole --add-data "config.json;." run.py



-----------------------------------------------
def convert_to_mp3(source_path, target_path):
    try:
        audio = AudioSegment.from_file(source_path)
        audio.export(target_path, format="mp3")
        print(f"🎧 Converted to MP3: {target_path}")
    except Exception as e:
        print(f"❌ Failed to convert {source_path} to MP3: {e}")


def download_file(filename):
    url = f"{GET_FILE_URL}/{filename}?token={TOKEN}"
    source_path = os.path.join(DEST_FOLDER, filename)
    mp3_path = os.path.join(DEST_FOLDER, filename.rsplit(".", 1)[0] + ".mp3")

    print(f"\n⬇ Downloading {filename}...")

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(source_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Saved to {source_path}")

        # Convert to MP3 (regardless of format)
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in [".ogg", ".mp4"]:
            convert_to_mp3(source_path, mp3_path)
            os.remove(source_path)
            print(f"🗑️ Deleted original file: {source_path}")
        else:
            print(f"⚠️ Unsupported file type: {file_ext} (skipped conversion)")

        return True
    except Exception as e:
        print(f"❌ Failed to download or convert {filename}: {e}")
        return False
        
