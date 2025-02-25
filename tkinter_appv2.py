import tkinter as tk
from tkinter import ttk
import threading
import queue
import sys
import file_handlerv5  # Updated handler with progress callback
from medical_db import search_database  # import the search function

# Define your database path
DB_PATH = r"C:\Users\Usuario\Desktop\server\medical_reports.db"

# A class to capture stdout and send it to a queue
class QueueOutput:
    def __init__(self, output_queue):
        self.queue = output_queue

    def write(self, s):
        if s.strip():
            self.queue.put(s)

    def flush(self):
        pass

# Function that runs file_handlerv5.main() in a separate thread with progress callback
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

# The main application container that handles switching between frames
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Almacenamiento de estudios")
        self.geometry("700x620")
        self.configure(bg="white")
        
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        self.frames = {}
        
        # Instantiate all frames and place them in the same location.
        for F in (MainMenu, UploadFrame, SearchFrame):
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(MainMenu)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

# Main menu frame with two buttons side-by-side
class MainMenu(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Create a frame to center the buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(expand=True)
        
        search_button = ttk.Button(button_frame, text="Buscar un estudio",
                                   command=lambda: controller.show_frame(SearchFrame))
        upload_button = ttk.Button(button_frame, text="Guardar Trabajo",
                                   command=lambda: controller.show_frame(UploadFrame))
        search_button.grid(row=0, column=0, padx=20, pady=20)
        upload_button.grid(row=0, column=1, padx=20, pady=20)

# Upload frame that contains your existing file processing UI
class UploadFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.frame = ttk.Frame(self, padding="10")
        self.frame.pack(fill="both", expand=True)
        
        # Back button to return to main menu
        back_button = ttk.Button(self.frame, text="Volver al Menu",
                                 command=lambda: controller.show_frame(MainMenu))
        back_button.pack(anchor="w")
        
        self.label = ttk.Label(self.frame, text="Progreso de procesamiento de archivos", background="white")
        self.label.pack(pady=5)
        
        self.progress = ttk.Progressbar(self.frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=5)
        
        self.text = tk.Text(self.frame, wrap="word", height=15, bg="lightyellow")
        self.text.pack(fill="both", expand=True, pady=5)
        
        self.process_button = ttk.Button(self.frame, text="Guardar archivos", command=self.start_processing)
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
            self.label.config(text=f"Progreso de procesamiento: {processed}/{total} pairs")
        self.after(100, self.update_progress_bar)

# Search frame for querying the sqlite database
class SearchFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Top area with a back button
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x")
        back_button = ttk.Button(top_frame, text="Back to Menu",
                                 command=lambda: controller.show_frame(MainMenu))
        back_button.pack(side="left", padx=10, pady=10)
        
        # Input fields for search parameters
        input_frame = ttk.Frame(self)
        input_frame.pack(pady=10, fill="x", padx=10)
        
        ttk.Label(input_frame, text="Cedula paciente:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.patient_id_entry = ttk.Entry(input_frame)
        self.patient_id_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(input_frame, text="Nombre paciente:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.patient_name_entry = ttk.Entry(input_frame)
        self.patient_name_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(input_frame, text="Fecha de Transcripcion:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.transcription_date_entry = ttk.Entry(input_frame)
        self.transcription_date_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        search_button = ttk.Button(input_frame, text="Buscar", command=self.perform_search)
        search_button.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Results display area with vertical scrollbar
        results_frame = ttk.Frame(self)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.results_text = tk.Text(results_frame, wrap="word", bg="lightgray")
        self.results_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.results_text.config(yscrollcommand=scrollbar.set)
    
    def perform_search(self):
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Retrieve search parameters (empty fields become None)
        patient_id = self.patient_id_entry.get().strip() or None
        patient_name = self.patient_name_entry.get().strip() or None
        transcription_date = self.transcription_date_entry.get().strip() or None
        
        try:
            result = search_database(DB_PATH, patient_id=patient_id,
                                     patient_name=patient_name,
                                     transcription_date=transcription_date)
        except Exception as e:
            self.results_text.insert(tk.END, f"Error en la busqueda: {e}\n")
            return
        
        results = result.get("results", [])
        if not results:
            self.results_text.insert(tk.END, "No hay resultados.\n")
        else:
            for record in results:
                self.results_text.insert(tk.END, "-" * 50 + "\n")
                for key, value in record.items():
                    self.results_text.insert(tk.END, f"{key}: {value}\n")
                self.results_text.insert(tk.END, "\n")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
