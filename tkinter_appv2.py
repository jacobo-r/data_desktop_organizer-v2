import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import sys
import os
import time
import pygame
import tkinter.font as tkFont
import shutil


import file_handlerv5  # Your existing file processing module
from medical_db import search_database  # For the search page

# Destination folder for verified file pairs

# --- Backend function for verifying a pair (from verify_match_backend.py) ---
# (Assume this function is imported from the verify_match_backend module in practice)
# ITS IN THE FILE_HANDLER
# --------------------------
# Existing classes: QueueOutput, run_processing, UploadFrame, SearchFrame
# --------------------------

db_path = r"C:\Users\Usuario\Desktop\server\medical_reports.db"
receiver_folder = r"C:\Users\Usuario\Desktop\receiver_folder2"

class QueueOutput:
    def __init__(self, output_queue):
        self.queue = output_queue

    def write(self, s):
        if s.strip():
            self.queue.put(s)

    def flush(self):
        pass

def run_processing(log_queue, progress_queue, finish_callback):
    original_stdout = sys.stdout
    sys.stdout = QueueOutput(log_queue)
    try:
        file_handlerv5.main(progress_callback=lambda processed, total: progress_queue.put((processed, total)))
    except Exception as e:
        log_queue.put(f"Exception: {e}\n")
    finally:
        sys.stdout.flush()
        sys.stdout = original_stdout
    finish_callback()

class UploadFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.frame = ttk.Frame(self, padding="10")
        self.frame.pack(fill="both", expand=True)
        
        back_button = ttk.Button(self.frame, text="Volver Menu",
                                 command=lambda: controller.show_frame(MainMenu))
        back_button.pack(anchor="w")
        
        self.label = ttk.Label(self.frame, text="Progreso de Guardado", background="white")
        self.label.pack(pady=5)
        
        self.progress = ttk.Progressbar(self.frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=5)
        
        self.text = tk.Text(self.frame, wrap="word", height=15, bg="lightyellow")
        self.text.pack(fill="both", expand=True, pady=5)
        
        self.process_button = ttk.Button(self.frame, text="Guardar todos los archivos", command=self.start_processing)
        self.process_button.pack(pady=5)
        
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.after(100, self.process_log_queue)
        self.after(100, self.update_progress_bar)
    
    def start_processing(self):
        self.text.delete(1.0, tk.END)
        self.process_button.config(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = 100  # Will be updated dynamically
        
        threading.Thread(target=run_processing, args=(self.log_queue, self.progress_queue, self.processing_finished), daemon=True).start()
    
    def processing_finished(self):
        self.after(0, self.finish_ui)
    
    def finish_ui(self):
        self.progress.stop()
        self.process_button.config(state="normal")
        self.text.delete(1.0, tk.END)
        self.text.tag_configure("center", justify='center')
        self.text.tag_configure("green", foreground="green", font=("Helvetica", 24, "bold"))
        self.text.insert(tk.END, "COMPLETADO\n", ("center", "green"))
    
    def process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.text.insert(tk.END, message + "\n")
            self.text.see(tk.END)
        self.after(100, self.process_log_queue)
    
    def update_progress_bar(self):
        while not self.progress_queue.empty():
            processed, total = self.progress_queue.get_nowait()
            self.progress["maximum"] = total
            self.progress["value"] = processed
            self.label.config(text=f"Processing progress: {processed}/{total} pairs")
        self.after(100, self.update_progress_bar)

def copy_files_to_desktop(audio_path, pdf_path):
    """
    Copies the audio_path and pdf_path to the user's desktop.
    """
    if not audio_path or not pdf_path:
        messagebox.showwarning("Advertencia", "No se encontró la ruta de audio o PDF en este registro.")
        return
    
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shutil.copy2(audio_path, desktop)
        shutil.copy2(pdf_path, desktop)
        messagebox.showinfo("Éxito", "Los archivos se copiaron al escritorio con éxito.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron copiar los archivos: {e}")

class SearchFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Top bar
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x")
        
        back_button = ttk.Button(top_frame, text="Volver al Menu",
                                 command=lambda: controller.show_frame(MainMenu))
        back_button.pack(side="left", padx=10, pady=10)
        
        # Search inputs
        input_frame = ttk.Frame(self)
        input_frame.pack(pady=10, fill="x", padx=10)
        
        ttk.Label(input_frame, text="Cédula Paciente:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.patient_id_entry = ttk.Entry(input_frame)
        self.patient_id_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(input_frame, text="Nombre Paciente:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.patient_name_entry = ttk.Entry(input_frame)
        self.patient_name_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(input_frame, text="Fecha de Transcripción:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.transcription_date_entry = ttk.Entry(input_frame)
        self.transcription_date_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        search_button = ttk.Button(input_frame, text="Search", command=self.perform_search)
        search_button.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Results container (scrollable)
        self.results_container = ttk.Frame(self)
        self.results_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 1) Create a Canvas and a Scrollbar
        self.results_canvas = tk.Canvas(self.results_container)
        self.results_canvas.pack(side="left", fill="both", expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.results_container, orient="vertical", command=self.results_canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        
        self.results_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 2) Create an inner frame inside the Canvas
        self.inner_frame = ttk.Frame(self.results_canvas)
        # The window on the canvas that will contain `self.inner_frame`
        self.canvas_window = self.results_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        # 3) Bind events to make the canvas scroll properly
        self.inner_frame.bind("<Configure>", self.on_frame_configure)
        self.results_canvas.bind("<Configure>", self.on_canvas_configure)
        
    def on_frame_configure(self, event):
        """
        Reset the scroll region to encompass the inner frame.
        """
        self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """
        When the canvas is resized, match the inner frame's width to the canvas's width.
        """
        canvas_width = event.width
        self.results_canvas.itemconfig(self.canvas_window, width=canvas_width)

    def perform_search(self):
        # Clear old results
        for child in self.inner_frame.winfo_children():
            child.destroy()
        
        patient_id = self.patient_id_entry.get().strip() or None
        patient_name = self.patient_name_entry.get().strip() or None
        transcription_date = self.transcription_date_entry.get().strip() or None
        
        try:
            result = search_database(
                db_path=db_path,
                patient_id=patient_id,
                patient_name=patient_name,
                transcription_date=transcription_date
            )
        except Exception as e:
            # If there's an error, just show one label
            ttk.Label(self.inner_frame, text=f"Error durante la búsqueda: {e}").pack(pady=5)
            return
        
        records = result.get("results", [])
        if not records:
            ttk.Label(self.inner_frame, text="No se encontró nada.").pack(pady=5)
        else:
            for idx, record in enumerate(records, start=1):
                self.create_result_item(record, idx)

    def create_result_item(self, record, index):
        """
        Creates a frame that shows the record info and a 'Copy to Desktop' button.
        """
        item_frame = ttk.Frame(self.inner_frame, relief="groove", borderwidth=2)
        item_frame.pack(fill="x", padx=5, pady=5)
        
        # Title or index
        header_label = ttk.Label(item_frame, text=f"Resultado #{index}", font=("Helvetica", 10, "bold"))
        header_label.pack(pady=(5, 2))
        
        # Show the record data as lines
        info_text = ""
        for key, value in record.items():
            info_text += f"{key}: {value}\n"
        
        info_label = ttk.Label(item_frame, text=info_text, justify="left")
        info_label.pack(padx=10, pady=2)
        
        # "Copy to Desktop" button
        audio_path = record.get("audio_file_path")
        pdf_path = record.get("pdf_file_path")
        
        copy_button = ttk.Button(
            item_frame, 
            text="Copiar al Escritorio", 
            command=lambda: copy_files_to_desktop(audio_path, pdf_path)
        )
        copy_button.pack(pady=5)
# --------------------------
# New VerifyMatchFrame for "Agregar Trabajo"
# --------------------------

class VerifyMatchFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        self.audio_played = False
        self.audio_play_start_time = None
        
        # File path variables
        self.audio_file_path = None
        self.pdf_file_path = None
        
        # Storage for extracted PDF info
        self.pdf_info = {}
        
        # Top bar with a back button
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=5)
        back_button = ttk.Button(top_frame, text="Volver al Menu",
                                 command=lambda: controller.show_frame(MainMenu))
        back_button.pack(side="left", padx=10)
        
        # Main content area with two side-by-side frames
        content_frame = ttk.Frame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left rectangle: Audio file selection and audio player
        audio_frame = ttk.LabelFrame(content_frame, text="Archivo Audio (.mp3)", width=300, height=200)
        audio_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        audio_frame.grid_propagate(False)
        
        self.audio_label = ttk.Label(audio_frame, text="Click para seleccionar Audio", background="lightblue")
        self.audio_label.place(relx=0.5, rely=0.5, anchor="center")
        self.audio_label.bind("<Button-1>", self.select_audio_file)
        
        audio_buttons_frame = ttk.Frame(content_frame)
        audio_buttons_frame.grid(row=1, column=0, padx=10, pady=5)
        self.play_button = ttk.Button(audio_buttons_frame, text="Reproducir Audio", command=self.play_audio, state="disabled")
        self.reset_button = ttk.Button(audio_buttons_frame, text="Reiniciar Audio", command=self.reset_audio, state="disabled")
        self.play_button.pack(side="left", padx=5)
        self.reset_button.pack(side="left", padx=5)
        
        # Right rectangle: PDF file selection and display of extracted info
        pdf_frame = ttk.LabelFrame(content_frame, text="Archivo PDF (Transcripcion)", width=300, height=200)
        pdf_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        pdf_frame.grid_propagate(False)
        
        self.pdf_label = ttk.Label(pdf_frame, text="Click para seleccionar archivo PDF", background="lightgreen")
        self.pdf_label.place(relx=0.5, rely=0.5, anchor="center")
        self.pdf_label.bind("<Button-1>", self.select_pdf_file)
        
        # Under the PDF area, show extracted info with tickboxes
        info_frame = ttk.Frame(content_frame)
        info_frame.grid(row=1, column=1, padx=10, pady=5)
        
        self.patient_name_var = tk.StringVar(value="Nombre del Paciente: No disponible")
        self.doctor_name_var = tk.StringVar(value="Doctor: No disponible")
        
        patient_frame = ttk.Frame(info_frame)
        patient_frame.pack(fill="x", pady=2)
        self.patient_label = ttk.Label(patient_frame, textvariable=self.patient_name_var)
        self.patient_label.pack(side="left", padx=5)
        self.patient_check_var = tk.BooleanVar(value=False)
        self.patient_check = ttk.Checkbutton(
            patient_frame, 
            variable=self.patient_check_var,
            text="Verificado", 
            state="disabled", 
            command=self.check_verification
        )
        self.patient_check.pack(side="left", padx=5)
        
        doctor_frame = ttk.Frame(info_frame)
        doctor_frame.pack(fill="x", pady=2)
        self.doctor_label = ttk.Label(doctor_frame, textvariable=self.doctor_name_var)
        self.doctor_label.pack(side="left", padx=5)
        self.doctor_check_var = tk.BooleanVar(value=False)
        self.doctor_check = ttk.Checkbutton(
            doctor_frame, 
            variable=self.doctor_check_var,
            text="Verificado", 
            state="disabled", 
            command=self.check_verification
        )
        self.doctor_check.pack(side="left", padx=5)
        
        # Instructions block
        instructions_frame = ttk.Frame(self)
        instructions_frame.pack(pady=10)
        
        instructions_text = (
            "INSTRUCCIONES:\n\n"
            "1. Haga clic en el recuadro azul para seleccionar el archivo de audio.\n"
            "2. Haga clic en el recuadro verde para seleccionar el PDF de la transcripción.\n"
            "3. Haga clic en \"Reproducir Audio\" y escuche al menos 2 segundos para confirmar\n"
            "   la voz del médico y el nombre del paciente.\n"
            "4. Si el nombre y el médico coinciden con lo que aparece en pantalla,\n"
            "   marque ambos campos como \"Verificado\".\n"
            "5. Finalmente, presione \"Verificar\" para guardar ambos archivos."
        )
        
        instructions_label = ttk.Label(
            instructions_frame, 
            text=instructions_text, 
            justify="center"
        )
        instructions_label.pack()
        
        # Verify Match button (initially locked)
        self.verify_button = ttk.Button(self, text="Verificar", command=self.verify_match, state="disabled")
        self.verify_button.pack(pady=10)
    
    def select_audio_file(self, event=None):
        file_path = filedialog.askopenfilename(title="Select Audio File", filetypes=[("MP3 files", "*.mp3")])
        if file_path:
            self.audio_file_path = file_path
            filename = os.path.basename(file_path)
            self.audio_label.config(text=filename)
            self.play_button.config(state="normal")
            self.reset_button.config(state="normal")
            self.audio_played = False
            self.audio_play_start_time = None
            self.patient_check_var.set(False)
            self.doctor_check_var.set(False)
            self.patient_check.config(state="disabled")
            self.doctor_check.config(state="disabled")
            self.verify_button.config(state="disabled")
    
    def select_pdf_file(self, event=None):
        file_path = filedialog.askopenfilename(title="Select PDF File", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.pdf_file_path = file_path
            filename = os.path.basename(file_path)
            self.pdf_label.config(text=filename)
            # Extract info from the PDF using get_requested_info from info_extractorv2
            try:
                from info_extractorv2 import get_requested_info
                self.pdf_info = get_requested_info(file_path)
            except Exception as e:
                self.pdf_info = {}
                messagebox.showerror("Error", f"Error extracting info from PDF: {e}")
            patient_name = self.pdf_info.get("Patient Name", "Not Available")
            doctor = self.pdf_info.get("Doctor", "Not Available")
            self.patient_name_var.set(f"Nombre del Paciente: {patient_name}")
            self.doctor_name_var.set(f"Doctor: {doctor}")
            self.patient_check_var.set(False)
            self.doctor_check_var.set(False)
            self.patient_check.config(state="disabled")
            self.doctor_check.config(state="disabled")
            self.verify_button.config(state="disabled")
    
    def play_audio(self):
        if self.audio_file_path:
            try:
                pygame.mixer.music.load(self.audio_file_path)
                pygame.mixer.music.play()
                self.audio_play_start_time = time.time()
                self.after(2100, self.check_audio_played)  # 2.1 seconds
            except Exception as e:
                messagebox.showerror("Error", f"Error playing audio: {e}")
    
    def reset_audio(self):
        pygame.mixer.music.stop()
        self.audio_play_start_time = None
        self.patient_check_var.set(False)
        self.doctor_check_var.set(False)
        self.patient_check.config(state="disabled")
        self.doctor_check.config(state="disabled")
        self.verify_button.config(state="disabled")
    
    def check_audio_played(self):
        if self.audio_play_start_time and (time.time() - self.audio_play_start_time >= 2):
            self.audio_played = True
            self.patient_check.config(state="normal")
            self.doctor_check.config(state="normal")
        else:
            # Keep checking every 0.5 seconds
            self.after(500, self.check_audio_played)
    
    def check_verification(self):
        if self.patient_check_var.get() and self.doctor_check_var.get():
            self.verify_button.config(state="normal")
        else:
            self.verify_button.config(state="disabled")
    
    def verify_match(self):
        if not self.audio_file_path or not self.pdf_file_path:
            messagebox.showwarning("Warning", "ATENCION: debe haber seleccionado un audio y un pdf.")
            return
        
        try:
            result = file_handlerv5.process_matched_files(self.pdf_file_path, self.audio_file_path)
            if result:
                messagebox.showinfo("Success", "Ambos archivos fueron verificados y guardados.")
                self.reset_ui()
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el procesamiento: {e}")
    
    def reset_ui(self):
        self.audio_file_path = None
        self.pdf_file_path = None
        self.audio_label.config(text="Click para seleccionar Audio")
        self.pdf_label.config(text="Click para seleccionar archivo PDF")
        self.play_button.config(state="disabled")
        self.reset_button.config(state="disabled")
        self.patient_name_var.set("Nombre del Paciente: No disponible")
        self.doctor_name_var.set("Doctor: No disponible")
        self.patient_check_var.set(False)
        self.doctor_check_var.set(False)
        self.patient_check.config(state="disabled")
        self.doctor_check.config(state="disabled")
        self.verify_button.config(state="disabled")
        self.audio_played = False
        self.audio_play_start_time = None
        pygame.mixer.music.stop()

# --------------------------
# Modified Main Menu and Main Application
# -------------------------

class MainMenu(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Configure a grid so each row expands equally.
        # We'll have 5 rows total:
        #   0: Title
        #   1: First Section (Emparejar)
        #   2: Second Section (Guardar)
        #   3: Third Section (Buscar)
        #   4: Fourth Section (Counter)
        for row_index in range(5):
            self.rowconfigure(row_index, weight=1)
        self.columnconfigure(0, weight=1)

        # 1) Title
        title_label = ttk.Label(
            self, 
            text="APLICACION PARA GUARDAR TRANSCRIPCIONES",
            font=("Helvetica", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=10)

        # 2) First Section: Emparejar Audio y PDF
        first_section = ttk.Frame(self)
        first_section.grid(row=1, column=0, sticky="nsew")
        self.create_first_section(first_section)

        # 3) Second Section: Guardar Estudios
        second_section = ttk.Frame(self)
        second_section.grid(row=2, column=0, sticky="nsew")
        self.create_second_section(second_section)

        # 4) Third Section: Buscar un Estudio
        third_section = ttk.Frame(self)
        third_section.grid(row=3, column=0, sticky="nsew")
        self.create_third_section(third_section)

        # 5) Fourth Section: Counter of not-yet-saved pairs
        fourth_section = ttk.Frame(self)
        fourth_section.grid(row=4, column=0, sticky="nsew")
        self.create_counter_section(fourth_section)

    def on_show(self):
        """
        This method is called each time the MainMenu is raised.
        We refresh the pending-count label here so it's always up to date.
        """
        self.refresh_pending_count()

    def create_first_section(self, container):
        """
        Creates the first section: instructions for pairing audio and PDF.
        """
        # Separator (optional, if you want a line above this section)
        # sep_top = ttk.Separator(container, orient="horizontal")
        # sep_top.pack(fill="x", pady=5)

        text_1 = (
            "1. Durante el dia, cada vez que haga una transcripción:\n"
            "   Debe venir aquí y cargar el audio que haya transcrito con el PDF\n"
            "   de la transcripción que le corresponde. Para cargar la pareja (audio-pdf), haga clic en:"
        )
        label_1 = ttk.Label(
            container, 
            text=text_1,
            wraplength=600,
            justify="center"
        )
        label_1.pack(pady=5)

        verify_button = ttk.Button(
            container,
            text="Emparejar Audio y PDF",
            command=lambda: self.controller.show_frame(VerifyMatchFrame)
        )
        verify_button.pack(pady=10)

    def create_second_section(self, container):
        """
        Creates the second section: instructions for saving all paired studies.
        """
        text_2 = (
            "2. Al final de su día de trabajo:\n"
            "   Una vez haya emparejado todos los estudios (audio y transcripción)\n"
            "   que hizo durante el día, guarde todo el trabajo del día aquí:"
        )
        label_2 = ttk.Label(
            container,
            text=text_2,
            wraplength=600,
            justify="center"
        )
        label_2.pack(pady=5)

        upload_button = ttk.Button(
            container,
            text="Guardar Estudios Emparejados",
            command=lambda: self.controller.show_frame(UploadFrame)
        )
        upload_button.pack(pady=10)

    def create_third_section(self, container):
        """
        Creates the third section: instructions for searching a saved study.
        """
        text_3 = "3. Para buscar un estudio (audio-pdf) guardado, haga clic en:"
        label_3 = ttk.Label(
            container,
            text=text_3,
            wraplength=600,
            justify="center"
        )
        label_3.pack(pady=5)

        search_button = ttk.Button(
            container,
            text="Buscar un Estudio",
            command=lambda: self.controller.show_frame(SearchFrame)
        )
        search_button.pack(pady=10)

    def create_counter_section(self, container):
        """
        Creates the fourth section: shows how many paired files
        are not yet saved in the final location.
        """
        sep = ttk.Separator(container, orient="horizontal")
        sep.pack(fill="x", pady=10)

        # Label
        label_4 = ttk.Label(
            container, 
            text="ESTUDIOS EMPAREJADOS QUE AÚN NO HA GUARDADO:",
            justify="center"
        )
        label_4.pack(pady=5)

        # A large green label to display the count
        self.pending_label_var = tk.StringVar(value="0")
        pending_label = ttk.Label(
            container,
            textvariable=self.pending_label_var,
            font=("Helvetica", 32, "bold"),
            foreground="green"
        )
        pending_label.pack(pady=10)

    def refresh_pending_count(self):
        """
        Reads the number of files in `receiver_folder`, divides by 2 (since each
        pair is two files), and updates the label accordingly.
        """
        try:
            files = os.listdir(receiver_folder)
            # If you only want to count .pdf and .mp3, for example:
            # files = [f for f in files if f.lower().endswith((".pdf", ".mp3"))]

            count = len(files) // 2
            self.pending_label_var.set(str(count))
        except Exception:
            # If there's an error (e.g. folder doesn't exist), just set to 0
            self.pending_label_var.set("0")



class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Almacenamiento de estudios")
        self.geometry("840x900")
        self.configure(bg="white")\
        
        # Increase the default font for all widgets
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(size=14)  # Increase size as needed
        self.option_add("*Font", default_font)
        
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        self.frames = {}
        
        # Add all frames: MainMenu, UploadFrame, SearchFrame, and VerifyMatchFrame
        for F in (MainMenu, UploadFrame, SearchFrame, VerifyMatchFrame):
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(MainMenu)

    def show_frame(self, cont):
        frame = self.frames[cont]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
