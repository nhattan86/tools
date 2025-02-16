import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pypdf import PdfReader, PdfWriter
import os

def convert_size_to_bytes(size, unit):
    """Converts size with unit (KB, MB, GB) to bytes."""
    unit = unit.lower()
    if unit == 'bytes' or unit == 'b':
        return size
    elif unit == 'kb':
        return size * 1024
    elif unit == 'mb':
        return size * 1024 * 1024
    elif unit == 'gb':
        return size * 1024 * 1024 * 1024
    else:
        raise ValueError("Invalid unit")

def convert_size(size_bytes):
    """Converts bytes to human-readable format (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        size_kb = round(size_bytes / 1024, 2)
        return f"{size_kb} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        size_mb = round(size_bytes / (1024 * 1024), 2)
        return f"{size_mb} MB"
    else:
        size_gb = round(size_bytes / (1024 * 1024 * 1024), 2)
        return f"{size_gb} GB"

def compress_pdf(input_path, output_path):
    """Compresses PDF file by rewriting content with pypdf."""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during PDF compression: {e}")
        return False

def select_pdf_file():
    """Opens file dialog to select PDF file and updates UI."""
    file_path = filedialog.askopenfilename(
        title="Select PDF File",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if file_path:
        input_pdf_path.set(file_path)
        original_size = os.path.getsize(file_path)
        original_size_label.config(text=f"Original Size: {convert_size(original_size)}")
        output_size_label.config(text="Compressed Size: Waiting for compression...")
        percentage_reduction_label.config(text="Size Reduction: Waiting for compression...")
        status_label.config(text="") # Clear previous status message

def start_compression():
    """Starts PDF compression based on user's choice and displays results."""
    input_file = input_pdf_path.get()
    if not input_file:
        messagebox.showerror("Error", "Please select a PDF file first.")
        return

    compression_type = compression_var.get()
    output_file = os.path.splitext(input_file)[0] + "_compressed.pdf" # Create output filename

    status_label.config(text="Compressing PDF...")
    window.update() # Update UI immediately to show status

    original_size = os.path.getsize(input_file)

    if compress_pdf(input_file, output_file):
        compressed_size = os.path.getsize(output_file)
        reduction_percentage = round((1 - (compressed_size / original_size)) * 100, 2)

        output_size_label.config(text=f"Compressed Size: {convert_size(compressed_size)}")
        percentage_reduction_label.config(text=f"Size Reduction: {reduction_percentage}%")
        status_label.config(text=f"Compression successful! Compressed file saved at: {output_file}")
        messagebox.showinfo("Success", f"PDF compression successful!\nCompressed file saved at:\n{output_file}")
    else:
        status_label.config(text="Compression failed. Please check error message.")

# Tkinter GUI setup
window = tk.Tk()
window.title("User-Friendly PDF Compressor")
window.geometry("450x400") # Slightly larger window

input_pdf_path = tk.StringVar()
compression_var = tk.StringVar(value='percentage') # Default to percentage reduction

# Program Title
title_label = tk.Label(window, text="Easy PDF Compressor", font=("Helvetica", 18, "bold"))
title_label.pack(pady=20)

# Select PDF File Button
select_button = tk.Button(window, text="Select PDF File", command=select_pdf_file)
select_button.pack(pady=10)

# Original Size Label
original_size_label = tk.Label(window, text="Original Size: No file selected")
original_size_label.pack()

# Compression Options Frame
options_frame = ttk.LabelFrame(window, text="Compression Options", padding=10)
options_frame.pack(pady=10, padx=20, fill="x")

# Percentage Reduction Radio Button and Entry
percentage_radio = tk.Radiobutton(options_frame, text="Reduce by Percentage:", variable=compression_var, value='percentage')
percentage_radio.grid(row=0, column=0, sticky="w")
percentage_entry = tk.Entry(options_frame, width=5)
percentage_entry.grid(row=0, column=1, padx=5, sticky="w")
percentage_label = tk.Label(options_frame, text="%")
percentage_label.grid(row=0, column=2, sticky="w")
percentage_entry.insert(0, "50") # Default percentage

# Target Size Radio Button and Entry with Unit Dropdown
target_size_radio = tk.Radiobutton(options_frame, text="Reduce to Target Size:", variable=compression_var, value='target_size')
target_size_radio.grid(row=1, column=0, sticky="w")
target_size_entry = tk.Entry(options_frame, width=8)
target_size_entry.grid(row=1, column=1, padx=5, sticky="w")
target_unit_options = ['KB', 'MB', 'GB']
target_unit_var = tk.StringVar(value=target_unit_options[1]) # Default to MB
target_unit_dropdown = ttk.Combobox(options_frame, textvariable=target_unit_var, values=target_unit_options, width=4)
target_unit_dropdown.grid(row=1, column=2, sticky="w")

# Output Size Label
output_size_label = tk.Label(window, text="Compressed Size: Waiting for compression...")
output_size_label.pack()

# Percentage Reduction Label
percentage_reduction_label = tk.Label(window, text="Size Reduction: Waiting for compression...")
percentage_reduction_label.pack()

# Compress PDF Button
compress_button = tk.Button(window, text="Compress PDF", command=start_compression)
compress_button.pack(pady=20)

# Status Label
status_label = tk.Label(window, text="")
status_label.pack()

window.mainloop()