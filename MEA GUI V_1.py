import tkinter as tk
from tkinter import filedialog, scrolledtext
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import threading
import queue
import os

class MEAGUI(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("MEA Ver. 1.0")
        self.geometry("800x600")

        # Set the application icon
        self.iconbitmap('image.ico')

        self.queue = queue.Queue()
        self.file_path_var = tk.StringVar()

        self.create_widgets()
        self.create_menu()

        # Enable drag-and-drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop)

        # Periodically check the queue for results
        self.after(100, self.process_queue)

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.open_button = tk.Button(top_frame, text="Open File", command=self.open_file)
        self.open_button.pack(side=tk.LEFT)

        credits_frame = tk.Frame(top_frame)
        credits_frame.pack(side=tk.RIGHT, anchor='ne')

        credit_label = tk.Label(credits_frame, text="Credit: MEA Copyright (C) 2014–2024 Plato Mavropoulos", anchor='e')
        credit_label.pack(anchor='e')

        credit_label_2 = tk.Label(credits_frame, text="MEA GUI by: Harshad Patel", anchor='e')
        credit_label_2.pack(anchor='e')

        self.file_path_label = tk.Label(top_frame, textvariable=self.file_path_var, anchor='w')
        self.file_path_label.pack(side=tk.LEFT, padx=10, pady=5)

        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD)
        self.output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.output_text.tag_configure('center', justify='center')
        self.output_text.tag_configure('configured', foreground='blue')
        self.output_text.tag_configure('unconfigured', foreground='brown')
        self.output_text.tag_configure('initialized', foreground='red')

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if file_path:
            self.file_path_var.set(f"Selected file: {file_path}")
            self.process_file(file_path)

    def drop(self, event):
        file_path = self.get_file_path(event.data)
        if file_path:
            self.file_path_var.set(f"Selected file: {file_path}")
            self.process_file(file_path)

    def get_file_path(self, dropped_data):
        file_path = dropped_data.strip('{}')
        if file_path.startswith("file:///"):
            file_path = file_path[8:]
        return file_path

    def process_file(self, file_path):
        self.output_text.delete(1.0, tk.END)
        threading.Thread(target=self.run_subprocess, args=(file_path,)).start()

    def run_subprocess(self, file_path):
        if os.path.exists('mea.exe'):
            command = ['mea.exe', file_path, '-skip']
        else:
            command = ['python', 'mea.py', file_path, '-skip']

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            output, error = process.communicate(input='\n')
            filtered_output = "\n".join(line for line in output.split("\n") if "Press enter to exit" not in line)
            self.queue.put((filtered_output, error))

        except Exception as e:
            self.queue.put((None, str(e)))

    def process_queue(self):
        try:
            while True:
                output, error = self.queue.get_nowait()
                if output:
                    start_index = self.output_text.index(tk.END)
                    self.output_text.insert(tk.END, output)
                    self.output_text.tag_add('center', '1.0', 'end')
                    self.highlight_text(start_index, "Configured", 'configured')
                    self.highlight_text(start_index, "Unconfigured", 'unconfigured')
                    self.highlight_text(start_index, "Initialized", 'initialized')

                if error:
                    self.output_text.insert(tk.END, f"\nError: {error}")
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def highlight_text(self, start_index, keyword, tag):
        pos = self.output_text.search(keyword, start_index, stopindex=tk.END)
        while pos:
            end_pos = f"{pos}+{len(keyword)}c"
            self.output_text.tag_add(tag, pos, end_pos)
            pos = self.output_text.search(keyword, end_pos, stopindex=tk.END)

if __name__ == "__main__":
    app = MEAGUI()
    app.mainloop()
