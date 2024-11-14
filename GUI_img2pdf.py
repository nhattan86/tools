# pip install Pillow

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

def convert_to_pdf():
    # Open a file dialog to select the image
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
    if not file_path:
        return

    try:
        # Open the image
        image = Image.open(file_path)

        # Convert to RGB if the image has transparency
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        # Save the image as a PDF
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", 
                                                     filetypes=[("PDF Files", "*.pdf")])
        if not output_path:
            return

        image.save(output_path)
        messagebox.showinfo("Success", f"Image converted to PDF and saved as {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Set up the main application window
root = tk.Tk()
root.title("Image to PDF Converter")
root.geometry("300x200")
root.configure(bg="#f0f0f0")

# Create a button to trigger the conversion
convert_button = tk.Button(root, text="Convert Image to PDF", command=convert_to_pdf, 
                            bg="#ffffff", fg="#000000", font=("Arial", 12))
convert_button.pack(pady=50)

# Start the GUI event loop
root.mainloop()
