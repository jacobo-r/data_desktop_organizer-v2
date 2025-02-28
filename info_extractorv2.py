import PyPDF2
import os
import re
import unicodedata
from datetime import datetime

# ------------------ CONFIG / DICTIONARIES ------------------ #
TRANSCRIBER_TOKENS = {
    "GALVIS MORALES JENIFFER": "JENIFFER",
    "GALVIS PEREZ DIANA CAROLINA": "CAROLINA",
    "OROZCO BARTOLO OSBALDO": "OSBALDO",
    "OPSINA ARANGO GLORIA NEIVER": "NEIVER",
    "RESTREPO CORREA JHONATAN": "JHONATAN",
    "RODRIGUEZ SERNA PAOLA ANDREA": "ANDREA",
    "TAFUR GONZALES SAMIR YANED": "YANED",
    "UTIMA PINEDA MARIA AMPARO": "AMPARO"
}

EXAM_TYPES = {
    "RADIOGRAFIA": ["RADIOGRAFIA", "RX"],
    "ECOGRAFIA": ["ECOGRAFIA", "ECO", "ECOS", "ECOGRAFIAS"],
    "TOMOGRAFIA": ["TOMOGRAFIA", "TAC", "TOMOGRAFIAS"],
    "ANGIOTOMRAFIA": ["ANGIOTOMRAFIA", "ANGIOTAC"],
    "RESONANCIA": ["RESONANCIA", "RM", "RMN", "RESONANCIAS"],
    "ANGIORESONANCIA": ["ANGIORESONANCIA"],
    "UROGRAFIA": ["UROGRAFIA"],
    "URETROCISTOGRAFIA": ["URETROCISTOGRAFIA"],
    "NEFROSTOMIA": ["NEFROSTOMIA"],
    "CAVOGRAFIA": ["CAVOGRAFIA"],
    "DRENAJE": ["DRENAJE"],
    "MAMOGRAFIA": ["MAMOGRAFIA", "MAMO"],
    "BIOPSIA": ["BIOPSIA"],
    "ANESTESIA": ["ANESTESIA"],
    "IMPLANTE": ["IMPLANTE"],
    "OCLUSION": ["OCLUSION"],
    "TORACENTESIS": ["TORACENTESIS"],
    "COLANGIORESONANCIA": ["COLANGIORESONANCIA"],
    "FLEBOGRAFIA": ["FLEBOGRAFIA"],
    "PARACENTESIS": ["PARACENTESIS"],
    "ELASTOGRAFIA": ["ELASTOGRAFIA"],
    "RETIRO": ["RETIRO"],
    "ANGIOPLASTIA": ["ANGIOPLASTIA"],
    "VENOGRAFIA": ["VENOGRAFIA"],
    "FARINGOGRAFIA": ["FARINGOGRAFIA"],
    "COLANGIOGRAFIA": ["COLANGIOGRAFIA"],
    "PANANGIOGRAFIA": ["PANANGIOGRAFIA"],
    "PIELOGRAFIA": ["PIELOGRAFIA"],
    "PERICARDIOCENTESIS": ["PERICARDIOCENTESIS"],
    "ARTRORESONANCIA": ["ARTRORESONANCIA"],
    "ARTERIOGRAFIA": ["ARTERIOGRAFIA"],
    "COLECISTOSTOMIA": ["COLECISTOSTOMIA"],
    "FLUOROSCOPIA": ["FLUOROSCOPIA", "FLURO"],
    "MARCAPASO": ["MARCAPASO"],
    "FISTULOGRAFIA": ["FISTULOGRAFIA"],
    "URETROGRAFIA": ["URETROGRAFIA"]
}

doctor_map = {
    "VICTOR HUGO RUIZ GRANADA":       ["RUIZ"],
    "JUAN CARLOS CORREA PUERTA":      ["CORREA"],
    "YESID CARDOZO VELEZ":            ["YESID", "CARDOZO"],
    "SANDRA LUCIA LOPEZ SIERRA":      ["SANDRA", "DANDRA"],
    "OSCAR ANDRES ALVAREZ GOMEZ":      ["OSCAR", "ALVAREZ"],
    "AGUSTO LEON ARIAS ZULUAGA":       ["ARIAS"],
    "JORGE AUGUSTO PULGARIN OSORIO":   ["PULGARIN"],
    "LYNDA IVETTE CARVAJAL ACOSTA":    ["LYNDA", "CARVAJAL"],
    "ALONSO GOMEZ GARCIA":             ["GOMEZ", "GARCIA", "ALONSO"],
    "JOSE FERNANDO VILLABONA GARCIA":   ["VILLABONA"],
    "FRANKLIN LEONARDO HANNA QUESADA":  ["HANNA"],
    "LUIS ALBERTO ROJAS":              ["ROJAS"],
    "CESAR YEPES":                     ["CESAR", "YEPES"],
    "LOREANNYS LORETYS OSPINO ORTIZ":   ["LOREANNYS", "OSPINO", "LOREANYS", "LOREANY"],
    "JUAN MANUEL TORO SANCHEZ":         ["TORO"],
    "CARLOS FELIPE HURTADO ARIAS":      ["HURTADO", "FELIPE", "HURTAO"]
}

# ------------------ HELPERS ------------------ #
def remove_accents(s: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFKD', s)
        if unicodedata.category(c) != 'Mn'
    )

def extract_patient_id(documento_text: str) -> str:
    """
    Identify any of the document types (CC, AS, CD, etc.) in the given text,
    then capture the first contiguous sequence of letters and/or digits immediately following.
    """
    pattern = r"\b(?:CC|AS|CD|CE|DN|DE|MS|NIT|PA|PE|PT|RC|SC|TI|SI)\b\s*[:\-]?\s*([A-Za-z0-9]+)"
    match = re.search(pattern, documento_text, re.IGNORECASE)
    return match.group(1) if match else ""

def find_transcriber_any_token(transcripcion: str) -> str:
    """
    Return the first transcriber from TRANSCRIBER_TOKENS whose unique token
    appears in the transcription (case-insensitive, accent-insensitive).
    """
    trans_norm = remove_accents(transcripcion).upper()
    for full_name, unique_token in TRANSCRIBER_TOKENS.items():
        token_norm = remove_accents(unique_token).upper()
        if token_norm in trans_norm:
            return full_name
    return ""

def find_transcription_date(transcripcion: str) -> str:
    """
    Extract the first DD/MM/YYYY from 'transcripcion'. Return empty if not found.
    """
    match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", transcripcion)
    return match.group(1) if match else ""

def find_exam_type(procedimiento: str) -> str:
    """
    Return the exam type from EXAM_TYPES if any of its keywords 
    appear in the 'procedimiento' text. Otherwise, return empty.
    """
    proc_norm = remove_accents(procedimiento).upper()
    for exam_key, keywords in EXAM_TYPES.items():
        for kw in keywords:
            kw_norm = remove_accents(kw).upper()
            if kw_norm in proc_norm:
                return exam_key
    return ""

def identify_doctor(paragraph_text: str) -> str:
    normalized = remove_accents(paragraph_text).lower()
    for doctor_name, keywords in doctor_map.items():
        for kw in keywords:
            kw_norm = remove_accents(kw).lower()
            if kw_norm in normalized:
                return doctor_name
    return ""

# ------------------ NEW: Robust Header Extraction ------------------ #
def extract_header_fields(header_text: str) -> dict:
    """
    Extract header fields from a block of text, allowing multi-line field values.
    """
    fields = {}
    norm_header = remove_accents(header_text).lower()

    patterns = {
        "paciente": r"paciente\s*:\s*(.*?)(?=\s+\w+\s*:|$)",
        "documento": r"documento\s*:\s*(.*?)(?=\s+\w+\s*:|$)",
        "entidad": r"entidad\s*:\s*(.*?)(?=\s+\w+\s*:|$)",
        "procedimiento": r"procedimiento\s*:\s*(.*?)(?=\s+\w+\s*:|$)",
        "fecha": r"fecha\s*:\s*(\d{2}/\d{2}/\d{4})",
        "nro_remision": r"nro\s+remisi(?:o|ó)n\s*:\s*(.*?)(?=\s+\w+\s*:|$)",
        "transcripcion": r"transcripci(?:o|ó)n\s*:\s*(.*?)(?=\s+\w+\s*:|$)"
    }

    # Use re.DOTALL to capture across multiple lines
    for field, pattern in patterns.items():
        match = re.search(pattern, norm_header, flags=re.IGNORECASE | re.DOTALL)
        if match:
            fields[field] = " ".join(match.group(1).split())  # Normalize whitespace
    return fields

# ------------------ PARSING THE PDF ------------------ #
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as f:
        pdf = PyPDF2.PdfReader(f)
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def parse_pdf_file(file_path: str) -> dict:
    fields = {
        "paciente": "",
        "documento": "",
        "entidad": "",
        "procedimiento": "",
        "fecha": "",
        "nro_remision": "",
        "transcripcion": "",
        "content_after_bars": "",
        "doctor": ""
    }
    
    pdf_text = extract_text_from_pdf(file_path)
    # Split the text into lines, treating each as a paragraph (adjust as needed)
    paragraphs = [line for line in pdf_text.splitlines() if line.strip()]
    
    # 1) Collect header paragraphs up until a known delimiter (e.g., HALLAZGOS, TÉCNICA, CONCLUSIÓN)
    header_lines = []
    delimiter_found = False
    for p in paragraphs:
        if re.search(r'\b(hallazgos|tecnica|conclusion)\b', remove_accents(p).lower()):
            delimiter_found = True
            break
        header_lines.append(p)
    header_text = " ".join(header_lines)
    header_fields = extract_header_fields(header_text)
    fields.update(header_fields)
    
    # 2) Collect main body after header for any additional content (if needed)
    body_lines = []
    start_index = len(header_lines) if delimiter_found else 0
    for p in paragraphs[start_index:]:
        if re.search(r'^(atte|atentamente|dra\.|dr\.)', remove_accents(p).lower()):
            break
        body_lines.append(p.strip())
    fields["content_after_bars"] = "\n".join(body_lines).strip()
    
    # 3) Identify doctor from bottom-up (using all paragraphs)
    for p in reversed(paragraphs):
        doctor_found = identify_doctor(p)
        if doctor_found:
            fields["doctor"] = doctor_found
            break

    return fields

def print_requested_fields(info: dict) -> None:
    paciente        = info.get("paciente", "").strip()
    fecha_creacion  = info.get("fecha", "").strip()
    transcripcion   = info.get("transcripcion", "").strip()
    procedimiento   = info.get("procedimiento", "").strip()

    patient_name        = paciente
    creation_date       = fecha_creacion
    transcription_date  = find_transcription_date(transcripcion)
    transcriber         = find_transcriber_any_token(transcripcion)
    exam_type           = find_exam_type(procedimiento)
    # Extract patient ID from the "documento" field using our helper
    documento_text = info.get("documento", "").strip()
    patient_id = extract_patient_id(documento_text)

    print(f"Patient Name: {patient_name}")
    print(f"Creation Date: {creation_date}")
    print(f"Transcription Date: {transcription_date}")
    print(f"Transcriber: {transcriber}")
    print(f"Exam Type: {exam_type}")
    print(f"Doctor: {info.get('doctor', '').strip()}")
    print(f"Patient ID: {patient_id}")
    print()  # blank line

def get_requested_info(file_path: str) -> dict:
    """
    Parse the specified PDF document and return a dictionary with:
      - 'Patient Name'
      - 'Creation Date'
      - 'Transcription Date'
      - 'Transcriber'
      - 'Exam Type'
      - 'Doctor'
      - 'Patient ID'
    
    The Patient ID is extracted from the "documento" field by searching for any of the document
    types (e.g. CC, AS, PA, etc.) followed by its value.
    """
    info = parse_pdf_file(file_path)
    
    patient_name = info.get("paciente", "").strip()
    creation_date = info.get("fecha", "").strip()
    transcripcion_text = info.get("transcripcion", "").strip()
    procedimiento_text = info.get("procedimiento", "").strip()
    doctor = info.get("doctor", "").strip()

    transcription_date = find_transcription_date(transcripcion_text)
    transcriber = find_transcriber_any_token(transcripcion_text)
    exam_type = find_exam_type(procedimiento_text)

    # Extract patient ID from the "documento" field using our helper function
    documento_text = info.get("documento", "").strip()
    patient_id = extract_patient_id(documento_text)

    return {
        "Patient Name": patient_name,
        "Creation Date": creation_date,
        "Transcription Date": transcription_date,
        "Transcriber": transcriber,
        "Exam Type": exam_type,
        "Doctor": doctor,
        "Patient ID": patient_id
    }

# ------------------ UNIT TESTS ------------------ #
import unittest

class TestFieldExtraction(unittest.TestCase):
    def test_header_extraction(self):
        header_text = """
        Paciente : ROMERO GARCIA JOSE HUMERTO Documento : CC - 1006964711 - Sexo : M - Edad : 30 Años
        Entidad : CLINICA DEL COUNTRY Procedimiento : RADIOGRAFIA DE TORAX Fecha : 08/07/2024   nro remisión : 889418
        Transcripción : OROZCO BARTOLO OSBALDO 10/07/2024
        """
        fields = extract_header_fields(header_text)
        self.assertEqual(fields["paciente"], "romero garcia jose humerto")
        self.assertEqual(fields["documento"], "cc - 1006964711")
        self.assertEqual(fields["entidad"], "clinica del country")
        self.assertEqual(fields["procedimiento"], "radiografia de torax")
        self.assertEqual(fields["fecha"], "08/07/2024")
        self.assertEqual(fields["nro_remision"], "889418")
        self.assertEqual(fields["transcripcion"], "orozco bartolo osbaldo 10/07/2024")

    def test_multiline_procedimiento(self):
        header_text = """
        Paciente : SANTACOLOMA AGUDELO JUAN DIEGO Documento : CC - 1088314698 - Sexo : M - Edad : 30 Años
        Entidad : SEGUROS DE VIDA SURAMERICANA S.A.
        Procedimiento : ECOGRAFIA DE ABDOMEN TOTAL (HIGADO PANCREAS VESICULA 
        VIAS BILIARES RIÑONES BAZO GRANDES VASOS PELVIS Y FLANCOS)
        Fecha : 10/10/2024 Nro remisión : 886595
        Transcripción : Gloria Neiver Ospina - 16/10/2024 12:18:54 -
        """
        fields = extract_header_fields(header_text)
        self.assertEqual(fields["procedimiento"],
                         "ecografia de abdomen total (higado pancreas vesicula vias biliares rinones bazo grandes vasos pelvis y flancos)")

if __name__ == "__main__":
    folder_path = r"C:\Users\Usuario\Desktop\receiver_folder"  # Adjust as needed
    # Uncomment the next line to run unit tests:
    # unittest.main()

    # Process all PDF files in the folder
    for fname in os.listdir(folder_path):
        if fname.lower().endswith(".pdf"):
            file_path = os.path.join(folder_path, fname)
            info = parse_pdf_file(file_path)
            print(f"--- {fname} ---")
            print_requested_fields(info)
