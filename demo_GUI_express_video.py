import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import threading
import time
import os

class VideoRecorder:
    def __init__(self):
        self.is_recording = False
        self.cap = None
        self.out = None
        self.video_thread = None

    def start_recording(self, duration, output_dir):
        self.is_recording = True
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Camera not accessible!")
            return

        # Define video codec and create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        output_file = os.path.join(output_dir, f"output_{int(time.time())}.avi")
        fps = 20.0
        frame_size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                      int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.out = cv2.VideoWriter(output_file, fourcc, fps, frame_size)

        def record_video():
            start_time = time.time()
            while self.is_recording and (time.time() - start_time) < duration:
                ret, frame = self.cap.read()
                if ret:
                    self.out.write(frame)
                    cv2.imshow("Recording", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    break
            self.stop_recording()

        self.video_thread = threading.Thread(target=record_video)
        self.video_thread.start()

    def stop_recording(self):
        self.is_recording = False
        if self.cap:
            self.cap.release()
        if self.out:
            self.out.release()
        cv2.destroyAllWindows()

def start_recording_action():
    try:
        duration = int(duration_var.get()) * 60  # Convert minutes to seconds
        if duration <= 0:
            raise ValueError("Duration must be positive.")
        output_dir = directory_var.get()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        recorder.start_recording(duration, output_dir)
    except ValueError as e:
        messagebox.showerror("Invalid Input", str(e))

def stop_recording_action():
    recorder.stop_recording()

# GUI
root = tk.Tk()
root.title("Video Recorder")

recorder = VideoRecorder()

# Duration
duration_label = ttk.Label(root, text="Duration (minutes):")
duration_label.grid(row=0, column=0, padx=10, pady=10)
duration_var = tk.StringVar()
duration_entry = ttk.Entry(root, textvariable=duration_var, width=10)
duration_entry.grid(row=0, column=1, padx=10, pady=10)

# Directory
directory_label = ttk.Label(root, text="Output Directory:")
directory_label.grid(row=1, column=0, padx=10, pady=10)
directory_var = tk.StringVar(value="videos")
directory_entry = ttk.Entry(root, textvariable=directory_var, width=30)
directory_entry.grid(row=1, column=1, padx=10, pady=10)

# Buttons
start_button = ttk.Button(root, text="Start Recording", command=start_recording_action)
start_button.grid(row=2, column=0, padx=10, pady=10)

stop_button = ttk.Button(root, text="Stop Recording", command=stop_recording_action)
stop_button.grid(row=2, column=1, padx=10, pady=10)

root.mainloop()
