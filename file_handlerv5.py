import os
from pathlib import Path
import shutil
from datetime import datetime

from medical_db import MedicalReportDB  # Use the provided DB interface
# Import your extraction function (now supports PDFs directly)
from info_extractorv2 import get_requested_info

# Folder with incoming files
receiver_folder = r"C:\Users\Usuario\Desktop\receiver_folder"

# Database configuration (creates the DB if it does not exist)
db_path = r"C:\Users\Usuario\Desktop\server\medical_reports.db"
db = MedicalReportDB(db_path=db_path)

# Allowed file extensions for the two types of files
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
DOC_EXTENSIONS = {".pdf"}

# Required fields for the info extraction
REQUIRED_FIELDS = [
    "Patient Name",
    "Creation Date",
    "Transcription Date",
    "Transcriber",
    "Exam Type",
    "Doctor",
    "Patient ID"
]

def process_two_files(doc_path: str, audio_path: str) -> None:
    """
    Process a pair of files (one audio, one document):
      1. Extract the required info using get_requested_info directly on the document.
      2. Validate that all REQUIRED_FIELDS are present.
      NO 3. Move the processed document to the designated PDF folder.
      4. Insert the record into the database. ()a3 is done here)
    """
    # --- Change 1: Remove conversion logic ---
    # Previously, we checked the file extension and converted PDFs to DOCX.
    # Now, we directly use the file (whether PDF or DOCX) because the extractor handles PDFs.
    info_dict = get_requested_info(doc_path)
    for field in REQUIRED_FIELDS:
        if not info_dict.get(field, "").strip():
            raise ValueError(f"Missing required field: {field}")

    # --- Change 3: Update database insertion ---
    # We now use final_pdf_path as the pdf_src_path, since the file has been moved.
    db.insert_record(
        patient_id=info_dict["Patient ID"],
        patient_name=info_dict["Patient Name"],
        medical_procedure=info_dict["Exam Type"],
        procedure_date=info_dict["Creation Date"],
        transcriptor=info_dict["Transcriber"],
        transcription_date=info_dict["Transcription Date"],
        doctor=info_dict["Doctor"],
        audio_src_path=audio_path,
        pdf_src_path=doc_path
    )

def main(progress_callback=None):
    print("Starting file handler for batch processing.")

    all_files = [os.path.join(receiver_folder, f) for f in os.listdir(receiver_folder)]
    if not all_files:
        print("No files found in receiver folder.")
        return

    # Group files by their base name (pair nomenclature remains intact)
    groups = {}
    for f in all_files:
        base = Path(f).stem
        groups.setdefault(base, []).append(f)

    total_groups = len(groups)
    processed_groups = 0

    for base, files in groups.items():
        if len(files) != 2:
            print(f"Error: File group '{base}' does not have exactly 2 files.")
            continue

        audio_file, doc_file = None, None
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in AUDIO_EXTENSIONS:
                audio_file = f
            elif ext in DOC_EXTENSIONS:
                doc_file = f

        if audio_file and doc_file:
            try:
                process_two_files(doc_file, audio_file)
                processed_groups += 1
                print(f"Processed group '{base}'.")
                if progress_callback:
                    progress_callback(processed_groups, total_groups)
            except Exception as e:
                print(f"Error processing group '{base}': {e}")

    print(f"Batch processing complete. Processed {processed_groups} groups out of {total_groups}.")
    db.close()

def process_matched_files(pdf_path, audio_path):
    """
    Processes the matched PDF and audio files:
      - Extracts PDF info using get_requested_info().
      - Uses the 'Patient Name' (spaces replaced with underscores) and the current date/time
        to build unique filenames.
      - Copies both files into destination_folder with the new names.
    """
    destination_folder= receiver_folder
    # Extract PDF info
    info = get_requested_info(pdf_path)
    patient_name = info.get("Patient Name", "unknown").strip().replace(" ", "_")
    
    # Build a unique filename using patient name and current datetime
    now = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    new_basename = f"{patient_name}_{now}"
    new_pdf_name = new_basename + ".pdf"
    new_audio_name = new_basename + ".mp3"
    
    # Destination paths
    dest_pdf = os.path.join(destination_folder, new_pdf_name)
    dest_audio = os.path.join(destination_folder, new_audio_name)
    
    # Copy the files to the destination folder
    shutil.copy2(pdf_path, dest_pdf)
    shutil.copy2(audio_path, dest_audio)
    
    return True

if __name__ == "__main__":
    main()
