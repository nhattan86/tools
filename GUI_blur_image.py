import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np

class ImageBlurApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Blur Application")
        
        # Initialize variables
        self.original_image = None
        self.display_image = None
        self.blur_zones = []
        self.current_selection = None
        self.drawing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Upload Image", command=self.upload_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Image", command=self.save_image).pack(side=tk.LEFT, padx=5)
        
        # Canvas for image display
        self.canvas = tk.Canvas(main_frame, width=800, height=600, bg='white')
        self.canvas.grid(row=1, column=0, padx=5, pady=5)
        
        # Blur controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Blur Controls", padding="5")
        controls_frame.grid(row=1, column=1, padx=5, pady=5, sticky="n")
        
        # Blur type
        ttk.Label(controls_frame, text="Blur Type:").grid(row=0, column=0, pady=5)
        self.blur_type = ttk.Combobox(controls_frame, values=["Gaussian", "Motion", "Average"])
        self.blur_type.set("Gaussian")
        self.blur_type.grid(row=0, column=1, pady=5)
        
        # Blur intensity
        ttk.Label(controls_frame, text="Blur Intensity:").grid(row=1, column=0, pady=5)
        self.blur_intensity = ttk.Scale(controls_frame, from_=1, to=50, orient=tk.HORIZONTAL)
        self.blur_intensity.grid(row=1, column=1, pady=5)
        
        # Color blur option
        ttk.Label(controls_frame, text="Color Blur:").grid(row=2, column=0, pady=5)
        self.color_button = ttk.Button(controls_frame, text="Select Color", command=self.choose_color)
        self.color_button.grid(row=2, column=1, pady=5)
        self.blur_color = None
        
        # Apply blur button
        ttk.Button(controls_frame, text="Apply Blur", command=self.apply_blur).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Canvas bindings
        self.canvas.bind("<Button-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        
    def upload_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
        )
        if file_path:
            self.original_image = Image.open(file_path)
            # Resize image to fit canvas while maintaining aspect ratio
            display_size = (800, 600)
            self.original_image.thumbnail(display_size, Image.Resampling.LANCZOS)
            self.display_image = ImageTk.PhotoImage(self.original_image)
            self.canvas.config(width=self.original_image.width, height=self.original_image.height)
            self.canvas.create_image(0, 0, anchor="nw", image=self.display_image)
            
    def choose_color(self):
        color = colorchooser.askcolor(title="Choose blur color")[0]
        if color:
            self.blur_color = color
            
    def start_selection(self, event):
        if self.original_image:
            self.drawing = True
            self.current_selection = [event.x, event.y, event.x, event.y]
            self.selection_rect = self.canvas.create_rectangle(
                *self.current_selection, outline="red", width=2
            )
            
    def update_selection(self, event):
        if self.drawing:
            self.current_selection[2] = event.x
            self.current_selection[3] = event.y
            self.canvas.coords(self.selection_rect, *self.current_selection)
            
    def end_selection(self, event):
        if self.drawing:
            self.drawing = False
            self.blur_zones.append(self.current_selection)
            
    def apply_blur(self):
        if not self.original_image or not self.blur_zones:
            return
            
        # Convert PIL image to OpenCV format
        img = cv2.cvtColor(np.array(self.original_image), cv2.COLOR_RGB2BGR)
        
        for zone in self.blur_zones:
            x1, y1, x2, y2 = map(int, zone)
            roi = img[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)]
            
            if self.blur_type.get() == "Gaussian":
                kernel_size = int(self.blur_intensity.get()) * 2 + 1
                blurred_roi = cv2.GaussianBlur(roi, (kernel_size, kernel_size), 0)
            elif self.blur_type.get() == "Motion":
                kernel_size = int(self.blur_intensity.get())
                kernel = np.zeros((kernel_size, kernel_size))
                kernel[int((kernel_size-1)/2), :] = np.ones(kernel_size)
                kernel = kernel / kernel_size
                blurred_roi = cv2.filter2D(roi, -1, kernel)
            else:  # Average blur
                kernel_size = int(self.blur_intensity.get()) * 2 + 1
                blurred_roi = cv2.blur(roi, (kernel_size, kernel_size))
                
            if self.blur_color:
                color_overlay = np.full_like(blurred_roi, self.blur_color)
                alpha = 0.5
                blurred_roi = cv2.addWeighted(blurred_roi, 1-alpha, color_overlay, alpha, 0)
                
            img[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)] = blurred_roi
            
        # Convert back to PIL format and update display
        result_image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        self.display_image = ImageTk.PhotoImage(result_image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.display_image)
        self.original_image = result_image
        self.blur_zones = []
        
    def save_image(self):
        if self.original_image:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), 
                          ("All files", "*.*")]
            )
            if file_path:
                self.original_image.save(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageBlurApp(root)
    root.mainloop()
