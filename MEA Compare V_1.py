import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import threading
import queue
import os

class MEAGUI(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("MEA Compare Ver. 1.0")
        self.geometry("1400x800")  # Adjust the window size for side by side view

        # Set the application icon
        self.iconbitmap('image.ico')

        self.queue1 = queue.Queue()
        self.queue2 = queue.Queue()
        self.file_path_var1 = tk.StringVar()
        self.file_path_var2 = tk.StringVar()
        self.sync_scroll_var = tk.BooleanVar()

        self.create_widgets()
        self.create_menu()

        # Enable drag-and-drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop)

        # Periodically check the queue for results
        self.after(100, self.process_queue)

    def create_widgets(self):
        # Create a Frame for the top section
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Open button in the upper left corner
        self.open_button = tk.Button(top_frame, text="Open Files", command=self.open_files)
        self.open_button.grid(row=0, column=0, padx=5, sticky='w')

        # File path displays next to the open button
        self.file_path_label1 = tk.Label(top_frame, textvariable=self.file_path_var1, anchor='w')
        self.file_path_label1.grid(row=0, column=1, padx=10, pady=5, sticky='w')

        self.file_path_label2 = tk.Label(top_frame, textvariable=self.file_path_var2, anchor='w')
        self.file_path_label2.grid(row=1, column=1, padx=10, pady=5, sticky='w')

        # Synchronous scroll checkbox
        self.sync_scroll_checkbox = tk.Checkbutton(top_frame, text="Synchronize Scrolling", variable=self.sync_scroll_var, command=self.toggle_sync_scroll)
        self.sync_scroll_checkbox.grid(row=1, column=0, padx=5, sticky='w')

        # Create a Frame for the credits in the upper right corner
        credits_frame = tk.Frame(self)
        credits_frame.place(relx=1.0, y=10, anchor='ne')

        credit_label = tk.Label(credits_frame, text="Credit: MEA Copyright (C) 2014–2024 Plato Mavropoulos", anchor='e')
        credit_label.pack(anchor='e')

        credit_label_2 = tk.Label(credits_frame, text="MEA GUI by: Harshad Patel", anchor='e')
        credit_label_2.pack(anchor='e')

        # Create a Frame for better alignment
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a vertical scrollbar
        scrollbar = tk.Scrollbar(main_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create ScrolledText widgets for displaying output side by side
        self.output_text1 = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.output_text1.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.output_text1.bind('<MouseWheel>', self.on_mousewheel)
        self.output_text1.bind('<Button-1>', self.sync_scroll_to_position)

        self.output_text2 = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.output_text2.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.output_text2.bind('<MouseWheel>', self.on_mousewheel)
        self.output_text2.bind('<Button-1>', self.sync_scroll_to_position)

        # Configure the scrollbar to work with both text areas
        scrollbar.config(command=self.yview)

        # Center align the text
        self.output_text1.tag_configure('center', justify='center')
        self.output_text1.tag_configure('configured', foreground='blue')  # Tag for 'Configured' text
        self.output_text1.tag_configure('unconfigured', foreground='brown')  # Tag for 'Unconfigured' text
        self.output_text1.tag_configure('initialized', foreground='red')  # Tag for 'Initialized' text

        self.output_text2.tag_configure('center', justify='center')
        self.output_text2.tag_configure('configured', foreground='blue')  # Tag for 'Configured' text
        self.output_text2.tag_configure('unconfigured', foreground='brown')  # Tag for 'Unconfigured' text
        self.output_text2.tag_configure('initialized', foreground='red')  # Tag for 'Initialized' text

    def yview(self, *args):
        self.output_text1.yview(*args)
        self.output_text2.yview(*args)

    def create_menu(self):
        # Create a menu bar
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # Create a File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

    def open_files(self):
        # Open a file dialog and get the selected file paths
        file_paths = filedialog.askopenfilenames(filetypes=[("All files", "*.*")])
        if len(file_paths) == 2:
            self.file_path_var1.set(f"Selected file 1: {file_paths[0]}")  # Display the first file path
            self.file_path_var2.set(f"Selected file 2: {file_paths[1]}")  # Display the second file path
            self.process_files(file_paths[0], file_paths[1])
        else:
            messagebox.showerror("Error", "Please select 2 files.")

    def drop(self, event):
        # Handle the dropped files
        print(f"Drop event data: {event.data}")  # Debugging statement
        file_paths = self.get_file_paths(event.data)
        if len(file_paths) == 2:
            print(f"Processed file paths: {file_paths}")  # Debugging statement
            self.file_path_var1.set(f"Selected file 1: {file_paths[0]}")  # Display the first file path
            self.file_path_var2.set(f"Selected file 2: {file_paths[1]}")  # Display the second file path
            self.process_files(file_paths[0], file_paths[1])
        else:
            messagebox.showerror("Error", "Please select 2 files.")

    def get_file_paths(self, dropped_data):
        # Extract file paths from dropped data
        file_paths = dropped_data.strip('{}').split('} {')  # Split by '} {' to correctly separate paths
        file_paths = [path.strip() for path in file_paths]  # Clean up each path
        return file_paths

    def process_files(self, file_path1, file_path2):
        # Clear the output text areas
        self.output_text1.delete(1.0, tk.END)
        self.output_text2.delete(1.0, tk.END)

        # Print debugging information
        print(f"Processing file 1: {file_path1}")  # Debugging statement
        print(f"Processing file 2: {file_path2}")  # Debugging statement

        # Run mea.exe or mea.py in separate threads to avoid blocking the GUI
        threading.Thread(target=self.run_subprocess, args=(file_path1, self.queue1)).start()
        threading.Thread(target=self.run_subprocess, args=(file_path2, self.queue2)).start()

    def run_subprocess(self, file_path, queue):
        # Determine if mea.exe exists, otherwise use mea.py
        if os.path.exists('mea.exe'):
            command = ['mea.exe', file_path, '-skip']
        else:
            command = ['python', 'mea.py', file_path, '-skip']

        # Run the command and capture the output
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            # Send the enter key to proceed with the file analysis
            output, error = process.communicate(input='\n')

            # Filter out the "Press enter to exit" line
            filtered_output = "\n".join(line for line in output.split("\n") if "Press enter to exit" not in line)

            # Put the filtered output in the queue
            queue.put((filtered_output, error))

        except Exception as e:
            queue.put((None, str(e)))

    def process_queue(self):
        try:
            while True:
                output1, error1 = self.queue1.get_nowait()
                output2, error2 = self.queue2.get_nowait()

                if output1:
                    # Insert output into the ScrolledText widget
                    start_index = self.output_text1.index(tk.END)
                    self.output_text1.insert(tk.END, output1)
                    self.output_text1.tag_add('center', '1.0', 'end')

                    # Find and tag the 'Configured', 'Unconfigured', and 'Initialized' text
                    self.highlight_text(self.output_text1, start_index, "Configured", 'configured')
                    self.highlight_text(self.output_text1, start_index, "Unconfigured", 'unconfigured')
                    self.highlight_text(self.output_text1, start_index, "Initialized", 'initialized')

                if error1:
                    self.output_text1.insert(tk.END, f"\nError: {error1}")

                if output2:
                    # Insert output into the ScrolledText widget
                    start_index = self.output_text2.index(tk.END)
                    self.output_text2.insert(tk.END, output2)
                    self.output_text2.tag_add('center', '1.0', 'end')

                    # Find and tag the 'Configured', 'Unconfigured', and 'Initialized' text
                    self.highlight_text(self.output_text2, start_index, "Configured", 'configured')
                    self.highlight_text(self.output_text2, start_index, "Unconfigured", 'unconfigured')
                    self.highlight_text(self.output_text2, start_index, "Initialized", 'initialized')

                if error2:
                    self.output_text2.insert(tk.END, f"\nError: {error2}")
        except queue.Empty:
            pass
        # Schedule the next check
        self.after(100, self.process_queue)

    def highlight_text(self, text_widget, start_index, keyword, tag):
        pos = text_widget.search(keyword, start_index, stopindex=tk.END)
        while pos:
            end_pos = f"{pos}+{len(keyword)}c"
            text_widget.tag_add(tag, pos, end_pos)
            pos = text_widget.search(keyword, end_pos, stopindex=tk.END)

    def toggle_sync_scroll(self):
        if self.sync_scroll_var.get():
            self.sync_scroll_texts()  # Ensure both text areas are aligned initially
        else:
            self.output_text1.yview_moveto(0)
            self.output_text2.yview_moveto(0)

    def on_mousewheel(self, event):
        if self.sync_scroll_var.get():
            self.output_text1.yview_scroll(int(-1*(event.delta/120)), "units")
            self.output_text2.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            event.widget.yview_scroll(int(-1*(event.delta/120)), "units")

    def sync_scroll_to_position(self, event):
        if self.sync_scroll_var.get():
            self.output_text1.yview_moveto(self.output_text2.yview()[0])
            self.output_text2.yview_moveto(self.output_text1.yview()[0])

    def sync_scroll_texts(self):
        first_text_yview = self.output_text1.yview()
        self.output_text2.yview_moveto(first_text_yview[0])

if __name__ == "__main__":
    app = MEAGUI()
    app.mainloop()
