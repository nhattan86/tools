import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
                           QVBoxLayout, QHBoxLayout, QFileDialog, QComboBox, 
                           QSlider, QColorDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

class VideoBlurApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Blur Tool")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 150px;
            }
            QSlider {
                height: 20px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #ddd;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
        """)
        
        # Initialize variables
        self.video_path = None
        self.cap = None
        self.current_frame = None
        self.blur_regions = []
        self.current_blur_type = "Gaussian"
        self.current_blur_color = (0, 0, 0)
        self.is_drawing = False
        self.start_pos = None
        self.end_pos = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create top toolbar
        toolbar = QHBoxLayout()
        
        # Add upload button
        self.upload_btn = QPushButton("Upload Video")
        self.upload_btn.clicked.connect(self.upload_video)
        toolbar.addWidget(self.upload_btn)
        
        # Add blur type selector
        self.blur_type = QComboBox()
        self.blur_type.addItems(["Gaussian", "Box", "Median", "Color"])
        self.blur_type.currentTextChanged.connect(self.change_blur_type)
        toolbar.addWidget(self.blur_type)
        
        # Add blur intensity slider
        self.blur_intensity = QSlider(Qt.Horizontal)
        self.blur_intensity.setMinimum(1)
        self.blur_intensity.setMaximum(50)
        self.blur_intensity.setValue(15)
        toolbar.addWidget(self.blur_intensity)
        
        # Add color picker button
        self.color_btn = QPushButton("Select Color")
        self.color_btn.clicked.connect(self.select_color)
        self.color_btn.setEnabled(False)
        toolbar.addWidget(self.color_btn)
        
        layout.addLayout(toolbar)
        
        # Add video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("border: 2px solid #ddd; background-color: #fff;")
        layout.addWidget(self.video_label)
        
        # Add bottom toolbar
        bottom_toolbar = QHBoxLayout()
        
        # Add save button
        self.save_btn = QPushButton("Save Video")
        self.save_btn.clicked.connect(self.save_video)
        self.save_btn.setEnabled(False)
        bottom_toolbar.addWidget(self.save_btn)
        
        # Add clear regions button
        self.clear_btn = QPushButton("Clear Regions")
        self.clear_btn.clicked.connect(self.clear_regions)
        self.clear_btn.setEnabled(False)
        bottom_toolbar.addWidget(self.clear_btn)
        
        layout.addLayout(bottom_toolbar)
        
        # Set up video timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        # Mouse events for region selection
        self.video_label.setMouseTracking(True)
        self.video_label.mousePressEvent = self.mouse_press
        self.video_label.mouseMoveEvent = self.mouse_move
        self.video_label.mouseReleaseEvent = self.mouse_release

    def calculate_scale_and_offset(self, frame_width, frame_height):
        """Calculate scaling factor and offset for coordinate mapping"""
        label_width = self.video_label.width()
        label_height = self.video_label.height()
        
        # Calculate scale factor while maintaining aspect ratio
        width_scale = label_width / frame_width
        height_scale = label_height / frame_height
        self.scale_factor = min(width_scale, height_scale)
        
        # Calculate offset for centered image
        scaled_width = frame_width * self.scale_factor
        scaled_height = frame_height * self.scale_factor
        self.offset_x = (label_width - scaled_width) / 2
        self.offset_y = (label_height - scaled_height) / 2

    def map_coordinates(self, x, y):
        """Map display coordinates to video frame coordinates"""
        if self.cap is None:
            return (0, 0)
            
        # Remove offset and scale back to video coordinates
        frame_x = (x - self.offset_x) / self.scale_factor
        frame_y = (y - self.offset_y) / self.scale_factor
        
        # Ensure coordinates are within frame bounds
        frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_x = max(0, min(frame_x, frame_width - 1))
        frame_y = max(0, min(frame_y, frame_height - 1))
        
        return (int(frame_x), int(frame_y))

    def upload_video(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", 
                                                 "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if file_name:
            self.video_path = file_name
            self.cap = cv2.VideoCapture(file_name)
            
            # Calculate initial scale and offset
            frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.calculate_scale_and_offset(frame_width, frame_height)
            
            self.timer.start(30)  # Update every 30ms
            self.save_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            if self.blur_type.currentText() == "Color":
                self.color_btn.setEnabled(True)

    def update_frame(self):
        if self.cap is None:
            return
            
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
            
        self.current_frame = frame.copy()
        
        # Apply blur to regions
        for region in self.blur_regions:
            x1, y1, x2, y2 = region['coords']
            # Ensure coordinates are in bounds and properly ordered
            x1, x2 = min(max(x1, 0), frame.shape[1]-1), min(max(x2, 0), frame.shape[1]-1)
            y1, y2 = min(max(y1, 0), frame.shape[0]-1), min(max(y2, 0), frame.shape[0]-1)
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
            
            # Ensure region has minimum size
            if x_max - x_min < 2 or y_max - y_min < 2:
                continue
                
            roi = frame[y_min:y_max, x_min:x_max]
            
            if roi.size == 0:  # Skip empty regions
                continue
                
            if region['type'] == "Color":
                roi[:] = region['color']
            else:
                kernel_size = self.blur_intensity.value()
                if kernel_size % 2 == 0:
                    kernel_size += 1
                    
                if region['type'] == "Gaussian":
                    roi = cv2.GaussianBlur(roi, (kernel_size, kernel_size), 0)
                elif region['type'] == "Box":
                    roi = cv2.blur(roi, (kernel_size, kernel_size))
                elif region['type'] == "Median":
                    roi = cv2.medianBlur(roi, kernel_size)
                    
                frame[y_min:y_max, x_min:x_max] = roi
        
        # Convert frame to QImage and display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)

    def mouse_press(self, event):
        if self.cap is None:
            return
        self.is_drawing = True
        self.start_pos = self.map_coordinates(event.x(), event.y())

    def mouse_move(self, event):
        if self.is_drawing:
            self.end_pos = self.map_coordinates(event.x(), event.y())
            self.update_frame()

    def mouse_release(self, event):
        if self.is_drawing:
            self.is_drawing = False
            self.end_pos = self.map_coordinates(event.x(), event.y())
            
            # Add blur region
            if self.start_pos and self.end_pos:
                region = {
                    'coords': (*self.start_pos, *self.end_pos),
                    'type': self.current_blur_type,
                    'color': self.current_blur_color if self.current_blur_type == "Color" else None
                }
                self.blur_regions.append(region)

    def change_blur_type(self, blur_type):
        self.current_blur_type = blur_type
        self.color_btn.setEnabled(blur_type == "Color")

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_blur_color = (color.blue(), color.green(), color.red())  # BGR format for OpenCV

    def clear_regions(self):
        self.blur_regions = []

    def save_video(self):
        if self.video_path is None:
            return
            
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", 
                                                   "Video Files (*.mp4)")
        if output_path:
            # Reset video to start
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Get video properties
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                    
                # Apply blur to regions
                for region in self.blur_regions:
                    x1, y1, x2, y2 = region['coords']
                    x1, x2 = min(max(x1, 0), frame.shape[1]-1), min(max(x2, 0), frame.shape[1]-1)
                    y1, y2 = min(max(y1, 0), frame.shape[0]-1), min(max(y2, 0), frame.shape[0]-1)
                    x_min, x_max = min(x1, x2), max(x1, x2)
                    y_min, y_max = min(y1, y2), max(y1, y2)
                    
                    if x_max - x_min < 2 or y_max - y_min < 2:
                        continue
                        
                    roi = frame[y_min:y_max, x_min:x_max]
                    
                    if roi.size == 0:
                        continue
                        
                    if region['type'] == "Color":
                        roi[:] = region['color']
                    else:
                        kernel_size = self.blur_intensity.value()
                        if kernel_size % 2 == 0:
                            kernel_size += 1
                            
                        if region['type'] == "Gaussian":
                            roi = cv2.GaussianBlur(roi, (kernel_size, kernel_size), 0)
                        elif region['type'] == "Box":
                            roi = cv2.blur(roi, (kernel_size, kernel_size))
                        elif region['type'] == "Median":
                            roi = cv2.medianBlur(roi, kernel_size)
                            
                        frame[y_min:y_max, x_min:x_max] = roi
                
                out.write(frame)
            
            out.release()

    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoBlurApp()
    window.show()
    sys.exit(app.exec_())