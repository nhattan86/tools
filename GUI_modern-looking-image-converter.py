import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import threading
import time

class ImageConverterApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Image Format Converter")
        self.app.geometry("800x600")
        
        # Set light theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Variables
        self.selected_file = tk.StringVar()
        self.output_format = tk.StringVar(value="PNG")
        self.quality = tk.IntVar(value=90)
        self.progress_value = tk.DoubleVar(value=0)
        self.is_converting = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main Frame
        main_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(main_frame, text="Image Format Converter", 
                            font=("Arial", 24, "bold"))
        title.pack(pady=10)
        
        # File Selection Area
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(fill="x", pady=10)
        
        file_entry = ctk.CTkEntry(file_frame, textvariable=self.selected_file,
                                 placeholder_text="Select an image file...",
                                 width=500)
        file_entry.pack(side="left", padx=10, pady=10)
        
        browse_btn = ctk.CTkButton(file_frame, text="Browse",
                                  command=self.browse_file)
        browse_btn.pack(side="right", padx=10)
        
        # Options Area
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        
        # Format Selection
        format_label = ctk.CTkLabel(options_frame, text="Output Format:")
        format_label.pack(pady=5)
        
        formats = ["PNG", "JPEG", "WebP", "BMP", "TIFF", "ICO"]
        format_menu = ctk.CTkOptionMenu(options_frame, variable=self.output_format,
                                      values=formats)
        format_menu.pack(pady=5)
        
        # Quality Slider
        quality_label = ctk.CTkLabel(options_frame, text="Quality:")
        quality_label.pack(pady=5)
        
        quality_slider = ctk.CTkSlider(options_frame, from_=1, to=100,
                                     variable=self.quality,
                                     number_of_steps=99)
        quality_slider.pack(pady=5)
        
        quality_value = ctk.CTkLabel(options_frame, 
                                   textvariable=self.quality)
        quality_value.pack(pady=5)
        
        # Progress Bar Frame
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(progress_frame, 
                                         text="Ready to convert...",
                                         font=("Arial", 12))
        self.progress_label.pack(pady=5)
        
        # Convert Button
        self.convert_btn = ctk.CTkButton(main_frame, text="Convert Image",
                                       command=self.start_conversion,
                                       height=40,
                                       font=("Arial", 16, "bold"))
        self.convert_btn.pack(pady=20)
        
        # Status Area
        self.status_label = ctk.CTkLabel(main_frame, text="Ready",
                                        font=("Arial", 12))
        self.status_label.pack(pady=10)

    def simulate_progress(self):
        self.progress_bar.start()
        steps = ['Reading image...', 'Processing...', 'Converting format...', 'Saving...']
        progress_step = 0.25
        
        for step in steps:
            if not self.is_converting:
                break
            self.progress_label.configure(text=step)
            time.sleep(0.5)  # Simulate processing time
            self.progress_value.set(self.progress_value.get() + progress_step)
            self.progress_bar.set(self.progress_value.get())
        
        self.progress_bar.stop()
            
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.ico")
            ]
        )
        if file_path:
            self.selected_file.set(file_path)
            
    def start_conversion(self):
        if self.is_converting:
            return
            
        self.is_converting = True
        self.convert_btn.configure(state="disabled")
        self.progress_value.set(0)
        self.progress_bar.set(0)
        
        # Start progress simulation in a separate thread
        progress_thread = threading.Thread(target=self.simulate_progress)
        progress_thread.start()
        
        # Start conversion in a separate thread
        convert_thread = threading.Thread(target=self.convert_image)
        convert_thread.start()
            
    def convert_image(self):
        input_path = self.selected_file.get()
        if not input_path:
            messagebox.showerror("Error", "Please select an image file!")
            self.reset_conversion_state()
            return
            
        try:
            # Open the image
            image = Image.open(input_path)
            
            # Get output path
            output_format = self.output_format.get().lower()
            output_path = filedialog.asksaveasfilename(
                defaultextension=f".{output_format}",
                filetypes=[(f"{output_format.upper()} files", f"*.{output_format}")],
                initialfile=f"converted.{output_format}"
            )
            
            if not output_path:
                self.reset_conversion_state()
                return
                
            # Convert and save
            if output_format == "jpeg":
                image = image.convert("RGB")
            
            image.save(output_path, 
                      quality=self.quality.get() if output_format in ["jpeg", "webp"] else None)
            
            # Complete the progress bar
            self.progress_value.set(1.0)
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="Conversion completed!")
            self.status_label.configure(
                text=f"Successfully converted to {output_format.upper()}!",
                text_color="green"
            )
            
            # Ask to open folder
            if messagebox.askyesno("Success", 
                                 "Image converted successfully! Open containing folder?"):
                os.startfile(os.path.dirname(output_path))
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_label.configure(text="Conversion failed!", text_color="red")
        finally:
            self.reset_conversion_state()
    
    def reset_conversion_state(self):
        self.is_converting = False
        self.convert_btn.configure(state="normal")
        self.progress_bar.stop()
    
    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = ImageConverterApp()
    app.run()