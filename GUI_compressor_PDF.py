import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pypdf import PdfReader, PdfWriter
import os

def convert_size(size_bytes):
    """Convert bytes to human-readable format (KB, MB, GB)."""
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

def compress_pdf(input_path, output_path, progress_bar, window):
    """Compress PDF file using pypdf.

    Note: pypdf's compression is basic and mainly streamlines PDF structure.
    For stronger compression (image re-compression, etc.), consider
    integrating external tools like Ghostscript or specialized libraries.
    """
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        total_pages = len(reader.pages)
        page_count = 0

        for page in reader.pages:
            writer.add_page(page)
            page_count += 1
            progress_percent = int((page_count / total_pages) * 100)
            progress_bar['value'] = progress_percent
            window.update_idletasks()  # Update progress bar visually

        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during PDF compression: {e}")
        return False

def select_pdf_file():
    """Open file dialog to select PDF and display original size."""
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
        status_label.config(text="") # Clear old status message
        compression_button.config(state=tk.NORMAL) # Enable compress button when file selected

def start_compression():
    """Initiate PDF compression based on user's choice and display results."""
    input_file = input_pdf_path.get()
    if not input_file:
        messagebox.showerror("Error", "Please select a PDF file first.")
        return

    compression_type = compression_var.get()
    compression_value_str = compression_value_entry.get()
    unit = unit_var.get()

    if not compression_value_str:
        messagebox.showerror("Error", "Please enter a compression value.")
        return

    try:
        compression_value = float(compression_value_str)
        if compression_value <= 0:
            raise ValueError("Compression value must be positive.")
    except ValueError:
        messagebox.showerror("Error", "Invalid compression value. Please enter a valid number.")
        return

    output_file = os.path.splitext(input_file)[0] + "_compressed.pdf"

    status_label.config(text="Compressing PDF...")
    compression_button.config(state=tk.DISABLED) # Disable button during compression
    window.update() # Update GUI to show status immediately
    progress_bar['value'] = 0 # Reset progress bar
    progress_bar.start(10) # Start indeterminate progress if needed, or keep at 0

    original_size = os.path.getsize(input_file)
    target_reduction_percent = None
    target_size_bytes = None

    if compression_type == "percentage":
        target_reduction_percent = compression_value
        # pypdf doesn't directly control percentage reduction.
        # We'll proceed with basic compression and report the actual reduction.
    elif compression_type == "size":
        if unit == "KB":
            target_size_bytes = compression_value * 1024
        elif unit == "MB":
            target_size_bytes = compression_value * 1024 * 1024
        elif unit == "GB":
            target_size_bytes = compression_value * 1024 * 1024 * 1024
        elif unit == "bytes":
            target_size_bytes = compression_value
        # pypdf doesn't guarantee reaching a specific target size.
        # We'll proceed with basic compression and report the achieved size.


    if compress_pdf(input_file, output_file, progress_bar, window):
        progress_bar.stop() # Stop indeterminate progress if used
        progress_bar['value'] = 100 # Ensure progress bar is full
        compressed_size = os.path.getsize(output_file)
        reduction_percentage = round((1 - (compressed_size / original_size)) * 100, 2)

        output_size_label.config(text=f"Compressed Size: {convert_size(compressed_size)}")
        percentage_reduction_label.config(text=f"Size Reduction: {reduction_percentage}%")
        status_label.config(text=f"Compression successful! Compressed file saved at: {output_file}")
        messagebox.showinfo("Success", f"PDF compression successful!\nCompressed file saved at:\n{output_file}")
    else:
        progress_bar.stop() # Stop indeterminate progress if used
        status_label.config(text="Compression failed. Please check error message.")
    compression_button.config(state=tk.NORMAL) # Re-enable compress button after process


# Tkinter GUI setup
window = tk.Tk()
window.title("Friendly PDF Compressor")
window.geometry("500x400") # Increased window size

input_pdf_path = tk.StringVar()
compression_var = tk.StringVar(value="percentage") # Default to percentage compression
unit_var = tk.StringVar(value="KB") # Default unit for size compression

# Title Label
title_label = tk.Label(window, text="PDF File Compressor", font=("Helvetica", 18, "bold"))
title_label.pack(pady=20)

# Select PDF Button
select_button = tk.Button(window, text="Select PDF File", command=select_pdf_file)
select_button.pack(pady=10)

# Original Size Label
original_size_label = tk.Label(window, text="Original Size: No file selected")
original_size_label.pack()

# Compression Options Frame
compression_frame = tk.Frame(window)
compression_frame.pack(pady=10)

# Percentage Radio Button
percentage_radio = tk.Radiobutton(compression_frame, text="Reduce by Percentage:", variable=compression_var, value="percentage")
percentage_radio.grid(row=0, column=0, sticky="w")

# Size Radio Button
size_radio = tk.Radiobutton(compression_frame, text="Reduce to Size (under):", variable=compression_var, value="size")
size_radio.grid(row=1, column=0, sticky="w")

# Compression Value Entry
compression_value_entry = tk.Entry(compression_frame, width=10)
compression_value_entry.grid(row=0, column=1, padx=5) # Default to percentage row initially

# Unit Dropdown (Combobox)
unit_options = ["bytes", "KB", "MB", "GB"]
unit_combobox = ttk.Combobox(compression_frame, textvariable=unit_var, values=unit_options, width=5)
unit_combobox.grid(row=1, column=2, padx=5) # Default to size row initially
unit_combobox.config(state=tk.DISABLED) # Disabled by default, enabled when 'size' is selected

def update_compression_ui():
    """Update UI elements based on selected compression type."""
    if compression_var.get() == "percentage":
        compression_value_entry.grid(row=0, column=1, padx=5)
        unit_combobox.grid_forget() # Hide unit combobox
        compression_value_entry.config(width=10) # Adjust width for percentage
    elif compression_var.get() == "size":
        compression_value_entry.grid(row=1, column=1, padx=5)
        unit_combobox.grid(row=1, column=2, padx=5) # Show unit combobox
        unit_combobox.config(state=tk.NORMAL) # Enable unit combobox
        compression_value_entry.config(width=7) # Adjust width for size value

percentage_radio.config(command=update_compression_ui)
size_radio.config(command=update_compression_ui)


# Compressed Size Label
output_size_label = tk.Label(window, text="Compressed Size: Waiting for compression...")
output_size_label.pack()

# Percentage Reduction Label
percentage_reduction_label = tk.Label(window, text="Size Reduction: Waiting for compression...")
percentage_reduction_label.pack()

# Progress Bar
progress_bar = ttk.Progressbar(window, orient=tk.HORIZONTAL, length=300, mode='determinate') # or 'indeterminate'
progress_bar.pack(pady=10)

# Compress Button
compression_button = tk.Button(window, text="Compress PDF", command=start_compression, state=tk.DISABLED) # Disabled initially
compression_button.pack(pady=20)

# Status Label
status_label = tk.Label(window, text="")
status_label.pack()


window.mainloop()