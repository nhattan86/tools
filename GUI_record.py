# pip install pillow opencv-python pygetwindow sounddevice numpy

import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab
import cv2
import numpy as np
import pygetwindow as gw
import sounddevice as sd
import wave
import threading
import time
import os
from datetime import datetime

class ScreenRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Recorder")
        self.root.geometry("400x500")
        
        # Biến điều khiển
        self.is_recording = False
        self.selected_window = None
        self.record_audio = False
        self.frame_count = 0
        self.start_time = 0
        
        self.setup_gui()
        
    def setup_gui(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Chọn cửa sổ để quay
        ttk.Label(main_frame, text="Chọn cửa sổ:").grid(row=0, column=0, pady=5, sticky=tk.W)
        self.window_combo = ttk.Combobox(main_frame, width=30)
        self.window_combo.grid(row=1, column=0, pady=5)
        self.update_window_list()
        
        # Checkbox quay âm thanh
        self.audio_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Quay âm thanh", variable=self.audio_var).grid(
            row=2, column=0, pady=5, sticky=tk.W
        )
        
        # Thông tin quay
        self.info_label = ttk.Label(main_frame, text="")
        self.info_label.grid(row=3, column=0, pady=5)
        
        # Nút điều khiển
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, pady=10)
        
        self.record_button = ttk.Button(
            control_frame, text="Bắt đầu quay", command=self.toggle_recording
        )
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Thoát", command=self.root.quit).pack(
            side=tk.LEFT, padx=5
        )

    def update_window_list(self):
        windows = gw.getAllTitles()
        self.window_combo['values'] = windows
        if windows:
            self.window_combo.set(windows[0])

    def get_window_position(self, window_title):
        try:
            window = gw.getWindowsWithTitle(window_title)[0]
            return {
                'left': window.left,
                'top': window.top,
                'width': window.width,
                'height': window.height
            }
        except:
            return None

    def start_recording(self):
        self.record_button.configure(text="Dừng quay")
        self.is_recording = True
        self.frame_count = 0
        self.start_time = time.time()
        
        # Tạo thư mục output nếu chưa có
        if not os.path.exists('recordings'):
            os.makedirs('recordings')
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_filename = f"recordings/screen_{timestamp}.avi"
        self.audio_filename = f"recordings/audio_{timestamp}.wav"
        
        window_info = self.get_window_position(self.window_combo.get())
        if not window_info:
            return
            
        # Khởi tạo writer video với XVID codec
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(
            self.video_filename,
            fourcc,
            30.0,
            (window_info['width'], window_info['height'])
        )
        
        # Khởi tạo recording âm thanh nếu được chọn
        if self.audio_var.get():
            self.audio_file = wave.open(self.audio_filename, 'wb')
            self.audio_file.setnchannels(2)
            self.audio_file.setsampwidth(2)
            self.audio_file.setframerate(44100)
            
            def audio_callback(indata, frames, time, status):
                if self.is_recording:
                    self.audio_file.writeframes(indata.tobytes())
            
            self.audio_stream = sd.InputStream(
                channels=2,
                samplerate=44100,
                dtype=np.int16,
                callback=audio_callback
            )
            self.audio_stream.start()
        
        # Bắt đầu thread quay video
        self.record_thread = threading.Thread(target=self.record_screen)
        self.record_thread.start()
        
        # Cập nhật thông tin
        self.update_info()

    def stop_recording(self):
        self.record_button.configure(text="Bắt đầu quay")
        self.is_recording = False
        
        if hasattr(self, 'video_writer'):
            self.video_writer.release()
            
        if self.audio_var.get() and hasattr(self, 'audio_stream'):
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_file.close()
            
        self.info_label.configure(text="Đã lưu bản ghi")

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def record_screen(self):
        window_info = self.get_window_position(self.window_combo.get())
        if not window_info:
            return
            
        while self.is_recording:
            # Chụp màn hình
            screen = ImageGrab.grab(bbox=(
                window_info['left'],
                window_info['top'],
                window_info['left'] + window_info['width'],
                window_info['top'] + window_info['height']
            ))
            
            # Chuyển đổi sang định dạng numpy array
            frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            # Ghi frame
            self.video_writer.write(frame)
            self.frame_count += 1

    def update_info(self):
        if self.is_recording:
            duration = int(time.time() - self.start_time)
            fps = self.frame_count / duration if duration > 0 else 0
            info_text = f"Đang quay: {duration}s\nFPS: {fps:.1f}"
            self.info_label.configure(text=info_text)
            self.root.after(1000, self.update_info)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenRecorder()
    app.run()
