import tkinter as tk
from tkinter import ttk
import threading
import queue
import sys
import file_handlerv5  # Updated handler with progress callback
import medical_db.search_database

# A class to capture stdout and send it to a queue
class QueueOutput:
    def __init__(self, output_queue):
        self.queue = output_queue

    def write(self, s):
        if s.strip():
            self.queue.put(s)

    def flush(self):
        pass

# Function that runs file_handler.main() in a separate thread with progress callback
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

# The main Tkinter GUI application
class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Processing GUI")
        self.geometry("600x400")
        self.configure(bg="white")
        
        self.frame = ttk.Frame(self, padding="10")
        self.frame.pack(fill="both", expand=True)
        
        self.label = ttk.Label(self.frame, text="File Processing Progress", background="white")
        self.label.pack(pady=5)
        
        self.progress = ttk.Progressbar(self.frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=5)
        
        self.text = tk.Text(self.frame, wrap="word", height=15, bg="lightyellow")
        self.text.pack(fill="both", expand=True, pady=5)
        
        self.process_button = ttk.Button(self.frame, text="Process Files", command=self.start_processing)
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

        # Clear the text widget and display "COMPLETADO" in green
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

if __name__ == "__main__":
    app = Application()
    app.mainloop()
