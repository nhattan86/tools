# pip install pygame

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import os
from PIL import Image, ImageTk
import pygame
import threading
import shutil

class VideoCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Frame Cropper")
        self.root.geometry("600x400")
        
        # Initialize pygame mixer for sound
        pygame.mixer.init()
        
        # Variables
        self.video_path = ""
        self.output_path = ""
        self.fps = tk.StringVar(value="1")
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Video selection
        ttk.Label(main_frame, text="Select Video:").grid(row=0, column=0, sticky=tk.W)
        self.video_label = ttk.Label(main_frame, text="No video selected")
        self.video_label.grid(row=0, column=1, sticky=tk.W)
        ttk.Button(main_frame, text="Browse", command=self.select_video).grid(row=0, column=2)
        
        # Output folder selection
        ttk.Label(main_frame, text="Save to:").grid(row=1, column=0, sticky=tk.W)
        self.output_label = ttk.Label(main_frame, text="No folder selected")
        self.output_label.grid(row=1, column=1, sticky=tk.W)
        ttk.Button(main_frame, text="Browse", command=self.select_output).grid(row=1, column=2)
        
        # FPS selection
        ttk.Label(main_frame, text="Frames per second:").grid(row=2, column=0, sticky=tk.W)
        fps_entry = ttk.Entry(main_frame, textvariable=self.fps, width=10)
        fps_entry.grid(row=2, column=1, sticky=tk.W)
        
        # Info display
        self.info_frame = ttk.LabelFrame(main_frame, text="Information", padding="5")
        self.info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.total_frames_label = ttk.Label(self.info_frame, text="Total frames: -")
        self.total_frames_label.grid(row=0, column=0, sticky=tk.W)
        
        self.size_label = ttk.Label(self.info_frame, text="Estimated size: -")
        self.size_label.grid(row=1, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Start button
        self.start_button = ttk.Button(main_frame, text="Start Cropping", command=self.start_cropping)
        self.start_button.grid(row=5, column=0, columnspan=3, pady=10)
        
    def select_video(self):
        self.video_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mkv")]
        )
        if self.video_path:
            self.video_label.config(text=os.path.basename(self.video_path))
            self.update_info()
            
    def select_output(self):
        self.output_path = filedialog.askdirectory()
        if self.output_path:
            self.output_label.config(text=self.output_path)
            
    def update_info(self):
        if self.video_path:
            cap = cv2.VideoCapture(self.video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = float(self.fps.get())
            frames_to_extract = int(total_frames / (cap.get(cv2.CAP_PROP_FPS) / fps))
            
            # Calculate estimated size (assuming JPG compression)
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            estimated_size = (frame_width * frame_height * 3 * frames_to_extract) / (1024 * 1024)  # In MB
            
            self.total_frames_label.config(text=f"Frames to extract: {frames_to_extract}")
            self.size_label.config(text=f"Estimated size: {estimated_size:.1f} MB")
            cap.release()
            
    def start_cropping(self):
        if not self.video_path or not self.output_path:
            messagebox.showerror("Error", "Please select video and output folder")
            return
            
        threading.Thread(target=self.crop_video, daemon=True).start()
        
    def crop_video(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            target_fps = float(self.fps.get())
            frame_interval = int(video_fps / target_fps)
            
            current_frame = 0
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if current_frame % frame_interval == 0:
                    output_file = os.path.join(self.output_path, f"frame_{frame_count:04d}.jpg")
                    cv2.imwrite(output_file, frame)
                    frame_count += 1
                    
                current_frame += 1
                progress = (current_frame / total_frames) * 100
                self.progress_var.set(progress)
                self.root.update_idletasks()
                
            cap.release()
            
            # Play success sound
            pygame.mixer.music.load("success.wav")  # Make sure to have this file
            pygame.mixer.music.play()
            
            messagebox.showinfo("Success", f"Successfully extracted {frame_count} frames!")
            self.progress_var.set(0)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.progress_var.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCropperApp(root)
    root.mainloop()
