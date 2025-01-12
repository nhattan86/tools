import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pdf2image import convert_from_path
import os
from PIL import Image, ImageTk
import threading
from pathlib import Path

class PDFConverter(tk.Tk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("PDF to Image Converter")
        self.geometry("800x600")
        self.configure(bg="#f0f0f0")

        # Style configuration
        self.style = ttk.Style()
        self.style.configure("Custom.TFrame", background="#f0f0f0")
        self.style.configure("Custom.TButton", 
                           padding=10, 
                           font=('Arial', 10, 'bold'),
                           background="#4CAF50")
        self.style.configure("Preview.TFrame", 
                           background="#ffffff",
                           relief="solid",
                           borderwidth=1)

        self.create_widgets()
        self.pdf_path = None
        self.preview_image = None
        self.current_page = 0
        self.total_pages = 0

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self, style="Custom.TFrame", padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File selection section
        file_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        file_frame.pack(fill=tk.X, pady=10)

        self.file_label = ttk.Label(
            file_frame, 
            text="No file selected",
            font=('Arial', 10),
            background="#f0f0f0"
        )
        self.file_label.pack(side=tk.LEFT, padx=5)

        select_btn = ttk.Button(
            file_frame,
            text="Select PDF",
            command=self.select_pdf,
            style="Custom.TButton"
        )
        select_btn.pack(side=tk.RIGHT, padx=5)

        # Settings frame
        settings_frame = ttk.LabelFrame(
            main_frame,
            text="Conversion Settings",
            style="Custom.TFrame",
            padding="10"
        )
        settings_frame.pack(fill=tk.X, pady=10)

        # Format selection
        format_frame = ttk.Frame(settings_frame, style="Custom.TFrame")
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            format_frame,
            text="Output Format:",
            background="#f0f0f0"
        ).pack(side=tk.LEFT, padx=5)
        
        self.format_var = tk.StringVar(value="PNG")
        self.format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.format_var,
            values=["PNG", "JPEG", "TIFF", "BMP"],
            state="readonly",
            width=10
        )
        self.format_combo.pack(side=tk.LEFT, padx=5)

        # DPI selection
        dpi_frame = ttk.Frame(settings_frame, style="Custom.TFrame")
        dpi_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            dpi_frame,
            text="DPI:",
            background="#f0f0f0"
        ).pack(side=tk.LEFT, padx=5)
        
        self.dpi_var = tk.StringVar(value="200")
        self.dpi_combo = ttk.Combobox(
            dpi_frame,
            textvariable=self.dpi_var,
            values=["100", "200", "300", "400", "500"],
            state="readonly",
            width=10
        )
        self.dpi_combo.pack(side=tk.LEFT, padx=5)

        # Preview frame
        preview_frame = ttk.LabelFrame(
            main_frame,
            text="Preview",
            style="Preview.TFrame",
            padding="10"
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Preview controls
        preview_controls = ttk.Frame(preview_frame, style="Custom.TFrame")
        preview_controls.pack(fill=tk.X, pady=5)

        self.prev_btn = ttk.Button(
            preview_controls,
            text="Previous",
            command=self.prev_page,
            state=tk.DISABLED,
            style="Custom.TButton"
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.page_label = ttk.Label(
            preview_controls,
            text="Page: 0/0",
            background="#f0f0f0"
        )
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(
            preview_controls,
            text="Next",
            command=self.next_page,
            state=tk.DISABLED,
            style="Custom.TButton"
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # Preview canvas
        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg="white",
            width=400,
            height=300
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # Convert button
        self.convert_btn = ttk.Button(
            main_frame,
            text="Convert",
            command=self.convert_pdf,
            style="Custom.TButton",
            state=tk.DISABLED
        )
        self.convert_btn.pack(pady=10)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

    def select_pdf(self):
        self.pdf_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if self.pdf_path:
            self.file_label.config(text=os.path.basename(self.pdf_path))
            self.convert_btn.config(state=tk.NORMAL)
            self.load_preview()

    def load_preview(self):
        try:
            # Convert first page for preview
            images = convert_from_path(
                self.pdf_path,
                dpi=100,
                first_page=1,
                last_page=1
            )
            self.total_pages = len(convert_from_path(
                self.pdf_path,
                dpi=100,
                first_page=1,
                last_page=None
            ))
            
            self.current_page = 0
            self.update_preview(images[0])
            self.update_navigation()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preview: {str(e)}")

    def update_preview(self, image):
        # Resize image to fit canvas
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # Calculate scaling factor
        width_scale = canvas_width / image.width
        height_scale = canvas_height / image.height
        scale = min(width_scale, height_scale)
        
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(resized)
        
        # Center image on canvas
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            x, y,
            anchor=tk.NW,
            image=self.preview_image
        )

    def update_navigation(self):
        self.page_label.config(text=f"Page: {self.current_page + 1}/{self.total_pages}")
        self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            images = convert_from_path(
                self.pdf_path,
                dpi=100,
                first_page=self.current_page + 1,
                last_page=self.current_page + 1
            )
            self.update_preview(images[0])
            self.update_navigation()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            images = convert_from_path(
                self.pdf_path,
                dpi=100,
                first_page=self.current_page + 1,
                last_page=self.current_page + 1
            )
            self.update_preview(images[0])
            self.update_navigation()

    def convert_pdf(self):
        if not self.pdf_path:
            return

        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return

        # Disable controls during conversion
        self.convert_btn.config(state=tk.DISABLED)
        self.format_combo.config(state=tk.DISABLED)
        self.dpi_combo.config(state=tk.DISABLED)

        def conversion_thread():
            try:
                images = convert_from_path(
                    self.pdf_path,
                    dpi=int(self.dpi_var.get())
                )
                
                total_images = len(images)
                for i, image in enumerate(images):
                    # Save image with selected format
                    output_path = os.path.join(
                        output_dir,
                        f"page_{i + 1}.{self.format_var.get().lower()}"
                    )
                    image.save(output_path)
                    
                    # Update progress
                    progress = ((i + 1) / total_images) * 100
                    self.progress_var.set(progress)
                    self.update()

                messagebox.showinfo(
                    "Success",
                    f"Converted {total_images} pages to {self.format_var.get()}"
                )

            except Exception as e:
                messagebox.showerror("Error", f"Conversion failed: {str(e)}")

            finally:
                # Re-enable controls
                self.convert_btn.config(state=tk.NORMAL)
                self.format_combo.config(state="readonly")
                self.dpi_combo.config(state="readonly")
                self.progress_var.set(0)

        # Start conversion in separate thread
        threading.Thread(target=conversion_thread, daemon=True).start()

if __name__ == "__main__":
    app = PDFConverter()
    app.mainloop()