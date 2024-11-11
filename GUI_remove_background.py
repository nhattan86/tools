import customtkinter as ctk
from rembg import remove
from PIL import Image, ImageTk
import os
from pathlib import Path
import threading
import time
from tkinter import filedialog
import io

class BackgroundRemoverGUI:
    def __init__(self):
        # Setup main window
        self.window = ctk.CTk()
        self.window.title("Background Remover Pro")
        self.window.geometry("1000x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize variables
        self.current_image = None
        self.processed_image = None
        self.image_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create main containers
        self.left_frame = ctk.CTkFrame(self.window, width=480)
        self.left_frame.pack(side="left", fill="both", padx=10, pady=10)
        
        self.right_frame = ctk.CTkFrame(self.window, width=480)
        self.right_frame.pack(side="right", fill="both", padx=10, pady=10)
        
        # Left frame components (Original Image)
        self.original_label = ctk.CTkLabel(self.left_frame, text="Original Image")
        self.original_label.pack(pady=5)
        
        self.original_image_label = ctk.CTkLabel(self.left_frame, text="No image selected")
        self.original_image_label.pack(pady=10)
        
        # Right frame components (Processed Image)
        self.processed_label = ctk.CTkLabel(self.right_frame, text="Processed Image")
        self.processed_label.pack(pady=5)
        
        self.processed_image_label = ctk.CTkLabel(self.right_frame, text="No image processed")
        self.processed_image_label.pack(pady=10)
        
        # Control panel
        self.control_frame = ctk.CTkFrame(self.window)
        self.control_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        # Buttons
        self.select_btn = ctk.CTkButton(
            self.control_frame, 
            text="Select Image", 
            command=self.select_image
        )
        self.select_btn.pack(side="left", padx=5)
        
        self.process_btn = ctk.CTkButton(
            self.control_frame, 
            text="Remove Background", 
            command=self.process_image,
            state="disabled"
        )
        self.process_btn.pack(side="left", padx=5)
        
        self.save_btn = ctk.CTkButton(
            self.control_frame, 
            text="Save Image", 
            command=self.save_image,
            state="disabled"
        )
        self.save_btn.pack(side="left", padx=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.control_frame)
        self.progress_bar.pack(side="left", padx=10, fill="x", expand=True)
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(self.control_frame, text="Ready")
        self.status_label.pack(side="right", padx=5)
        
    def select_image(self):
        self.image_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if self.image_path:
            self.current_image = Image.open(self.image_path)
            # Resize image to fit display
            display_image = self.resize_image_for_display(self.current_image)
            photo = ImageTk.PhotoImage(display_image)
            
            self.original_image_label.configure(image=photo, text="")
            self.original_image_label.image = photo
            
            self.process_btn.configure(state="normal")
            self.status_label.configure(text="Image loaded")
            
    def process_image(self):
        self.process_btn.configure(state="disabled")
        self.select_btn.configure(state="disabled")
        self.status_label.configure(text="Processing...")
        self.progress_bar.start()
        
        # Process image in separate thread
        thread = threading.Thread(target=self.remove_background)
        thread.start()
        
    def remove_background(self):
        try:
            # Remove background
            self.processed_image = remove(self.current_image)
            
            # Display processed image
            display_image = self.resize_image_for_display(self.processed_image)
            photo = ImageTk.PhotoImage(display_image)
            
            self.processed_image_label.configure(image=photo, text="")
            self.processed_image_label.image = photo
            
            self.window.after(0, self.processing_complete)
            
        except Exception as e:
            self.window.after(0, lambda: self.status_label.configure(
                text=f"Error: {str(e)}")
            )
            
    def processing_complete(self):
        self.progress_bar.stop()
        self.progress_bar.set(1)
        self.status_label.configure(text="Processing complete")
        self.process_btn.configure(state="normal")
        self.select_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        
    def save_image(self):
        if self.processed_image:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("All files", "*.*")
                ]
            )
            
            if save_path:
                self.processed_image.save(save_path)
                self.status_label.configure(text="Image saved successfully")
                
    def resize_image_for_display(self, image, max_size=(400, 400)):
        # Calculate aspect ratio
        aspect_ratio = image.width / image.height
        
        if image.width > max_size[0] or image.height > max_size[1]:
            if aspect_ratio > 1:
                return image.resize((max_size[0], int(max_size[0] / aspect_ratio)))
            else:
                return image.resize((int(max_size[1] * aspect_ratio), max_size[1]))
        return image
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = BackgroundRemoverGUI()
    app.run()