import tkinter as tk
from tkinter import ttk, filedialog
import cv2
import os
import numpy as np
from datetime import datetime, timedelta
from ttkthemes import ThemedTk

class VideoToImagesGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video to Images Converter")
        self.root.geometry("800x700")
        
        # Configure the theme and styles
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Subtitle.TLabel", font=("Helvetica", 11))
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        style.configure("Custom.TButton", font=("Helvetica", 10))
        style.configure("Status.TLabel", font=("Helvetica", 10, "italic"))
        
        # Initialize variables
        self.video_path = None
        self.recording = False
        self.cap = None
        self.output_path = None
        self.recording_start_time = None
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        ttk.Label(self.main_frame, text="Video to Images Converter", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Create sections using LabelFrame for better organization
        self.create_source_section()
        self.create_webcam_settings_section()
        self.create_extraction_settings_section()
        self.create_output_settings_section()
        
        # Video info frame
        self.video_info_frame = ttk.LabelFrame(self.main_frame, text="Video Information", padding="10")
        self.video_info_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 5))
        
        self.video_duration_label = ttk.Label(self.video_info_frame, text="Duration: --:--:--")
        self.video_duration_label.grid(row=0, column=0, pady=5)
        
        self.video_resolution_label = ttk.Label(self.video_info_frame, text="Resolution: ---x---")
        self.video_resolution_label.grid(row=0, column=1, pady=5, padx=(20, 0))
        
        # Status and Process button
        self.status_label = ttk.Label(self.main_frame, text="", style="Status.TLabel")
        self.status_label.grid(row=9, column=0, columnspan=2, pady=5)
        
        self.process_btn = ttk.Button(self.main_frame, text="Process Video",
                                    command=self.process_video, style="Custom.TButton")
        self.process_btn.grid(row=10, column=0, columnspan=2, pady=10)
        
        # Recording timer label
        self.timer_label = ttk.Label(self.main_frame, text="Recording Time: 00:00:00")
        self.timer_label.grid(row=11, column=0, columnspan=2, pady=5)
        self.timer_label.grid_remove()

    def create_source_section(self):
        source_frame = ttk.LabelFrame(self.main_frame, text="Video Source", padding="10")
        source_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.source_var = tk.StringVar(value="upload")
        ttk.Radiobutton(source_frame, text="Upload Video", variable=self.source_var, 
                       value="upload", command=self.handle_source_change).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(source_frame, text="Record from Webcam", variable=self.source_var,
                       value="webcam", command=self.handle_source_change).grid(row=0, column=1, padx=10)
        
        self.upload_btn = ttk.Button(source_frame, text="Choose Video", 
                                   command=self.upload_video, style="Custom.TButton")
        self.upload_btn.grid(row=1, column=0, columnspan=2, pady=(10,0))
        
        self.record_frame = ttk.Frame(source_frame)
        self.record_btn = ttk.Button(self.record_frame, text="Start Recording", 
                                   command=self.toggle_recording, style="Custom.TButton")
        self.record_btn.pack(pady=5)
        self.record_frame.grid(row=1, column=0, columnspan=2, pady=(10,0))
        self.record_frame.grid_remove()

    def create_webcam_settings_section(self):
        self.webcam_settings_frame = ttk.LabelFrame(self.main_frame, text="Webcam Settings", padding="10")
        self.webcam_settings_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.webcam_settings_frame.grid_remove()
        
        # Webcam resolution presets
        ttk.Label(self.webcam_settings_frame, text="Recording Resolution:").grid(row=0, column=0, pady=5)
        self.webcam_resolution_var = tk.StringVar(value="640x480")
        resolutions = ['640x480', '800x600', '1280x720', '1920x1080']
        resolution_combo = ttk.Combobox(self.webcam_settings_frame, 
                                      textvariable=self.webcam_resolution_var,
                                      values=resolutions, state="readonly")
        resolution_combo.grid(row=0, column=1, pady=5, padx=10)

    def create_extraction_settings_section(self):
        extraction_frame = ttk.LabelFrame(self.main_frame, text="Extraction Settings", padding="10")
        extraction_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # FPS settings
        ttk.Label(extraction_frame, text="FPS for extraction:").grid(row=0, column=0, pady=5)
        self.fps_var = tk.StringVar(value="1")
        fps_entry = ttk.Entry(extraction_frame, textvariable=self.fps_var, width=10)
        fps_entry.grid(row=0, column=1, pady=5, padx=10)
        self.fps_var.trace('w', self.update_image_count)
        
        self.image_count_label = ttk.Label(extraction_frame, text="Number of images: 0")
        self.image_count_label.grid(row=1, column=0, columnspan=2, pady=5)

    def create_output_settings_section(self):
        output_frame = ttk.LabelFrame(self.main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Resolution settings
        ttk.Label(output_frame, text="Output Resolution:").grid(row=0, column=0, pady=5)
        self.resolution_var = tk.StringVar(value="default")
        ttk.Radiobutton(output_frame, text="Default", variable=self.resolution_var,
                       value="default", command=self.toggle_resolution).grid(row=0, column=1)
        ttk.Radiobutton(output_frame, text="Custom", variable=self.resolution_var,
                       value="custom", command=self.toggle_resolution).grid(row=0, column=2)
        
        # Custom resolution frame
        self.resolution_frame = ttk.Frame(output_frame)
        ttk.Label(self.resolution_frame, text="Width:").grid(row=0, column=0)
        self.width_var = tk.StringVar(value="640")
        ttk.Entry(self.resolution_frame, textvariable=self.width_var, width=8).grid(row=0, column=1)
        ttk.Label(self.resolution_frame, text="Height:").grid(row=0, column=2, padx=(10,0))
        self.height_var = tk.StringVar(value="480")
        ttk.Entry(self.resolution_frame, textvariable=self.height_var, width=8).grid(row=0, column=3)
        self.resolution_frame.grid(row=1, column=0, columnspan=3, pady=5)
        self.resolution_frame.grid_remove()
        
        # Output directory
        ttk.Button(output_frame, text="Select Output Directory",
                  command=self.choose_output_directory, style="Custom.TButton").grid(
                      row=2, column=0, columnspan=3, pady=(10,0))

    def handle_source_change(self):
        if self.source_var.get() == "upload":
            self.upload_btn.grid()
            self.record_frame.grid_remove()
            self.webcam_settings_frame.grid_remove()
            self.timer_label.grid_remove()
        else:
            self.upload_btn.grid_remove()
            self.record_frame.grid()
            self.webcam_settings_frame.grid()
            self.timer_label.grid()

    def update_timer(self):
        if self.recording and self.recording_start_time:
            elapsed_time = datetime.now() - self.recording_start_time
            self.timer_label.config(text=f"Recording Time: {str(elapsed_time).split('.')[0]}")
            self.root.after(1000, self.update_timer)

    def start_recording(self):
        self.recording = True
        self.record_btn.config(text="Stop Recording")
        self.video_path = f"recorded_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        
        # Get selected resolution
        width, height = map(int, self.webcam_resolution_var.get().split('x'))
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(self.video_path, fourcc, 20.0, (width, height))
        
        self.recording_start_time = datetime.now()
        self.update_timer()
        self.record_frame_update()

    def stop_recording(self):
        self.recording = False
        self.record_btn.config(text="Start Recording")
        if self.cap is not None:
            self.cap.release()
        if hasattr(self, 'out'):
            self.out.release()
        cv2.destroyAllWindows()
        self.update_image_count()
        self.update_video_info()
        self.status_label.config(text=f"Video recorded: {self.video_path}")

    def update_video_info(self):
        if self.video_path:
            cap = cv2.VideoCapture(self.video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = timedelta(seconds=frame_count/fps)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.video_duration_label.config(text=f"Duration: {str(duration).split('.')[0]}")
            self.video_resolution_label.config(text=f"Resolution: {width}x{height}")
            cap.release()

    def upload_video(self):
        self.video_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")])
        if self.video_path:
            self.update_image_count()
            self.update_video_info()
            self.status_label.config(text=f"Selected video: {os.path.basename(self.video_path)}")

    # The rest of the methods remain the same as in the previous version
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.recording = True
        self.record_btn.config(text="Stop Recording")
        self.video_path = f"recorded_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        
        self.cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(self.video_path, fourcc, 20.0, (640,480))
        
        self.record_frame_update()

    def record_frame_update(self):
        if self.recording:
            ret, frame = self.cap.read()
            if ret:
                self.out.write(frame)
                cv2.imshow('Recording', frame)
                self.root.after(10, self.record_frame_update)

    def stop_recording(self):
        self.recording = False
        self.record_btn.config(text="Start Recording")
        if self.cap is not None:
            self.cap.release()
        if hasattr(self, 'out'):
            self.out.release()
        cv2.destroyAllWindows()
        self.update_image_count()
        self.status_label.config(text=f"Video recorded: {self.video_path}")

    def toggle_resolution(self):
        if self.resolution_var.get() == "custom":
            self.resolution_frame.grid()
        else:
            self.resolution_frame.grid_remove()

    def update_image_count(self, *args):
        if self.video_path and self.fps_var.get().isdigit():
            cap = cv2.VideoCapture(self.video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(self.fps_var.get())
            if fps > 0:
                num_images = total_frames // (cap.get(cv2.CAP_PROP_FPS) // fps)
                self.image_count_label.config(text=f"Number of images: {int(num_images)}")
            cap.release()

    def choose_output_directory(self):
        self.output_path = filedialog.askdirectory()
        if self.output_path:
            self.status_label.config(text=f"Output directory: {self.output_path}")

    def process_video(self):
        if not all([self.video_path, self.output_path, self.fps_var.get().isdigit()]):
            self.status_label.config(text="Please fill in all required fields")
            return

        cap = cv2.VideoCapture(self.video_path)
        fps = int(self.fps_var.get())
        frame_interval = int(cap.get(cv2.CAP_PROP_FPS) // fps)
        
        custom_size = None
        if self.resolution_var.get() == "custom":
            try:
                width = int(self.width_var.get())
                height = int(self.height_var.get())
                custom_size = (width, height)
            except ValueError:
                self.status_label.config(text="Invalid resolution values")
                return

        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                if custom_size:
                    frame = cv2.resize(frame, custom_size)
                
                filename = os.path.join(self.output_path, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(filename, frame)
                saved_count += 1

            frame_count += 1

        cap.release()
        self.status_label.config(text=f"Successfully saved {saved_count} images")


def main():
    root = ThemedTk(theme="breeze")  # You can choose different themes: 'arc', 'equilux', 'breeze', etc.
    app = VideoToImagesGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
