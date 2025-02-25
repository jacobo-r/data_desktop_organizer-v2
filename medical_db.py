import sqlite3
import os
import shutil

class MedicalReportDB:
    def __init__(self, db_path='medical_reports.db'):
        self.db_path = db_path
        self.base_folder = os.path.join(os.path.dirname(os.path.abspath(db_path)), 'db_files')
        self.audio_folder = os.path.join(self.base_folder, 'audios')
        self.pdf_folder = os.path.join(self.base_folder, 'pdfs')
        os.makedirs(self.audio_folder, exist_ok=True)
        os.makedirs(self.pdf_folder, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL CHECK(length(patient_id) <= 20),
                patient_name TEXT NOT NULL,
                medical_procedure TEXT NOT NULL CHECK(length(medical_procedure) <= 18),
                procedure_date TEXT NOT NULL,
                transcriptor TEXT NOT NULL CHECK(length(transcriptor) <= 28),
                transcription_date TEXT NOT NULL,
                doctor TEXT NOT NULL CHECK(length(doctor) <= 31),
                audio_file_path TEXT NOT NULL,
                pdf_file_path TEXT NOT NULL
            );
        ''')
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_patient_id ON medical_reports(patient_id);")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_patient_name ON medical_reports(patient_name);")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcription_date ON medical_reports(transcription_date);")

        self.conn.commit()

    def insert_record(self, patient_id, patient_name, medical_procedure, procedure_date, transcriptor, transcription_date, doctor, audio_src_path, pdf_src_path):
        """Insert a record into the database and store files in db_files folder."""
        try:
            self.cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='medical_reports';")
            last_id = self.cursor.fetchone()
            new_id = last_id[0] + 1 if last_id else 1

            file_base = f"{patient_id}_{procedure_date.replace('/', '-')}_{doctor.replace(' ', '_')}_{new_id}"
            audio_file_name = file_base + ".mp3"
            pdf_file_name = file_base + ".pdf"

            audio_file_path = self._store_file(audio_src_path, self.audio_folder, audio_file_name)
            pdf_file_path = self._store_file(pdf_src_path, self.pdf_folder, pdf_file_name)

            self.cursor.execute('''
                INSERT INTO medical_reports (
                    patient_id, patient_name, medical_procedure, procedure_date,
                    transcriptor, transcription_date, doctor, audio_file_path, pdf_file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patient_id, patient_name, medical_procedure, procedure_date, transcriptor, transcription_date, doctor, audio_file_path, pdf_file_path))
            self.conn.commit()
            print(f"Record inserted successfully for patient: {patient_name}.")
        except Exception as e:
            print(f"Failed to insert record for patient {patient_name}: {e}")
            # If storing failed, ensure files remain in original folder
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            if os.path.exists(pdf_file_path):
                os.remove(pdf_file_path)

    def _store_file(self, src_path, dest_folder, file_name):
        """Store the file in db_files structure and remove from original folder."""
        dest_path = os.path.join(dest_folder, file_name)
        shutil.move(src_path, dest_path)
        return dest_path

    def search_records(self, **kwargs):
        """Search records based on provided fields."""
        conditions = []
        values = []
        for field, value in kwargs.items():
            conditions.append(f"{field} LIKE ?")
            values.append(f"%{value}%")

        query = "SELECT * FROM medical_reports"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        self.cursor.execute(query, values)
        return self.cursor.fetchall()

    def close(self):
        """Close the database connection."""
        self.conn.close()


def search_database(db_path, patient_id=None, patient_name=None, transcription_date=None):
    """
    Search the medical_reports database based on patient_id, patient_name, or transcription_date.
    Returns a dictionary containing the results of the search.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Build dynamic query based on provided inputs
    conditions = []
    values = []

    if patient_id:
        conditions.append("patient_id LIKE ?")
        values.append(f"%{patient_id}%")

    if patient_name:
        conditions.append("patient_name LIKE ?")
        values.append(f"%{patient_name}%")

    if transcription_date:
        conditions.append("transcription_date LIKE ?")
        values.append(f"%{transcription_date}%")

    query = "SELECT * FROM medical_reports"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, values)
    results = cursor.fetchall()

    conn.close()

    # Prepare the dictionary of results
    search_results = []
    for row in results:
        search_results.append({
            "record_id": row[0],
            "patient_id": row[1],
            "patient_name": row[2],
            "medical_procedure": row[3],
            "procedure_date": row[4],
            "transcriptor": row[5],
            "transcription_date": row[6],
            "doctor": row[7],
            "audio_file_path": row[8],
            "pdf_file_path": row[9]
        })

    return {"results": search_results}