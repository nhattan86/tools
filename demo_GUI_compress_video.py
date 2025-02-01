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
        self.output_dir = "" # Store output directory for potential reuse or access
        self.output_file = "" # Store output file path for potential reuse or access

    def start_recording(self, duration_minutes, output_dir):
        if self.is_recording:
            messagebox.showinfo("Info", "Recording is already in progress.")
            return

        try:
            duration_seconds = int(duration_minutes) * 60
            if duration_seconds <= 0:
                raise ValueError("Duration must be a positive number.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive integer for duration.")
            return

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                messagebox.showerror("Error", f"Could not create output directory: {e}")
                return

        self.output_dir = output_dir # Store for later use if needed
        timestamp = int(time.time())
        self.output_file = os.path.join(output_dir, f"output_{timestamp}.avi")

        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise IOError("Cannot open webcam")

            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            fps = 20.0
            frame_size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                          int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            self.out = cv2.VideoWriter(self.output_file, fourcc, fps, frame_size)
            if not self.out.isOpened():
                raise IOError("Cannot open video writer")

            self.is_recording = True

            def record_video():
                start_time = time.time()
                while self.is_recording and (time.time() - start_time) < duration_seconds:
                    ret, frame = self.cap.read()
                    if ret:
                        self.out.write(frame)
                        cv2.imshow("Recording", frame)
                    else:
                        print("Error: Frame not captured. Stopping recording.") # For debugging in console
                        messagebox.showerror("Camera Error", "Could not read frame from camera. Recording stopped.")
                        break # Exit loop if frame not captured
                    if cv2.waitKey(1) & 0xFF == ord('q'): # Allow manual quit from recording window (optional)
                        self.stop_recording()
                        break
                self.stop_recording() # Ensure stop_recording is called when duration ends or loop breaks

            self.video_thread = threading.Thread(target=record_video)
            self.video_thread.start()
            start_button.config(state=tk.DISABLED) # Disable start button during recording
            stop_button.config(state=tk.NORMAL)   # Enable stop button during recording
            status_label.config(text="Recording...", foreground="red") # Update status label

        except IOError as e:
            self.stop_recording() # Ensure resources are released even if start fails
            messagebox.showerror("Error", f"Error starting recording: {e}")
        except cv2.error as e: # Catch OpenCV specific errors
            self.stop_recording()
            messagebox.showerror("OpenCV Error", f"OpenCV error during recording: {e}")
        except Exception as e: # Catch any other unexpected errors
            self.stop_recording()
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")


    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.video_thread and self.video_thread.is_alive():
                self.video_thread.join() # Wait for the thread to finish

        if self.cap:
            self.cap.release()
            self.cap = None # Reset cap to None

        if self.out:
            self.out.release()
            self.out = None # Reset out to None

        cv2.destroyAllWindows()
        start_button.config(state=tk.NORMAL)  # Enable start button after recording stops
        stop_button.config(state=tk.DISABLED) # Disable stop button after recording stops
        status_label.config(text="Ready", foreground="green") # Update status label
        messagebox.showinfo("Info", f"Recording stopped. Video saved to: {self.output_file}")


def start_recording_action():
    duration_str = duration_entry.get()
    output_dir = directory_entry.get()
    try:
        duration = int(duration_str)
        recorder.start_recording(duration, output_dir)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid integer for duration.")

def stop_recording_action():
    recorder.stop_recording()

# GUI Setup
root = tk.Tk()
root.title("Simple Video Recorder")

recorder = VideoRecorder()

# Duration Input
duration_label = ttk.Label(root, text="Duration (minutes):")
duration_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
duration_entry = ttk.Entry(root, width=10)
duration_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
duration_entry.insert(0, "1") # Default duration of 1 minute

# Directory Input
directory_label = ttk.Label(root, text="Output Directory:")
directory_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
directory_entry = ttk.Entry(root, width=40)
directory_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
directory_entry.insert(0, "videos") # Default directory

# Status Label
status_label = ttk.Label(root, text="Ready", foreground="green")
status_label.grid(row=2, column=0, columnspan=2, pady=5)

# Buttons Frame
buttons_frame = ttk.Frame(root)
buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)

start_button = ttk.Button(buttons_frame, text="Start Recording", command=start_recording_action)
start_button.pack(side=tk.LEFT, padx=10)

stop_button = ttk.Button(buttons_frame, text="Stop Recording", command=stop_recording_action, state=tk.DISABLED) # Initially disabled
stop_button.pack(side=tk.LEFT, padx=10)


root.mainloop()
