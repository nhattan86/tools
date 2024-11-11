import customtkinter as ctk
from pytube import YouTube, Playlist
import requests
import re
import threading
import os
from tkinter import messagebox
import json
from datetime import datetime

class VideoDownloaderGUI:
    def __init__(self):
        # Initialize main window
        self.window = ctk.CTk()
        self.window.title("Advanced Video Downloader")
        self.window.geometry("900x700")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize variables
        self.current_downloads = []
        self.download_history = self.load_download_history()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # URL Input Section
        self.url_frame = ctk.CTkFrame(self.main_frame)
        self.url_frame.pack(fill="x", padx=10, pady=10)
        
        self.url_label = ctk.CTkLabel(self.url_frame, text="Video URL:")
        self.url_label.pack(side="left", padx=5)
        
        self.url_entry = ctk.CTkEntry(self.url_frame, width=400)
        self.url_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Platform Selection
        self.platform_var = ctk.StringVar(value="youtube")
        self.platform_frame = ctk.CTkFrame(self.main_frame)
        self.platform_frame.pack(fill="x", padx=10, pady=5)
        
        self.youtube_radio = ctk.CTkRadioButton(
            self.platform_frame, 
            text="YouTube",
            variable=self.platform_var,
            value="youtube"
        )
        self.youtube_radio.pack(side="left", padx=20)
        
        self.facebook_radio = ctk.CTkRadioButton(
            self.platform_frame, 
            text="Facebook",
            variable=self.platform_var,
            value="facebook"
        )
        self.facebook_radio.pack(side="left", padx=20)
        
        # Quality Selection
        self.quality_frame = ctk.CTkFrame(self.main_frame)
        self.quality_frame.pack(fill="x", padx=10, pady=5)
        
        self.quality_label = ctk.CTkLabel(self.quality_frame, text="Quality:")
        self.quality_label.pack(side="left", padx=5)
        
        self.quality_var = ctk.StringVar(value="highest")
        self.quality_menu = ctk.CTkOptionMenu(
            self.quality_frame,
            variable=self.quality_var,
            values=["highest", "720p", "480p", "360p", "lowest"]
        )
        self.quality_menu.pack(side="left", padx=5)
        
        # Download Type
        self.type_frame = ctk.CTkFrame(self.main_frame)
        self.type_frame.pack(fill="x", padx=10, pady=5)
        
        self.type_var = ctk.StringVar(value="video")
        self.video_radio = ctk.CTkRadioButton(
            self.type_frame, 
            text="Video",
            variable=self.type_var,
            value="video"
        )
        self.video_radio.pack(side="left", padx=20)
        
        self.audio_radio = ctk.CTkRadioButton(
            self.type_frame, 
            text="Audio Only",
            variable=self.type_var,
            value="audio"
        )
        self.audio_radio.pack(side="left", padx=20)
        
        # Download Button
        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="Download",
            command=self.start_download
        )
        self.download_btn.pack(pady=10)
        
        # Progress Section
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.status_label.pack(pady=5)
        
        # Download History
        self.history_frame = ctk.CTkFrame(self.main_frame)
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.history_label = ctk.CTkLabel(self.history_frame, text="Download History")
        self.history_label.pack(pady=5)
        
        self.history_textbox = ctk.CTkTextbox(self.history_frame, height=200)
        self.history_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.update_history_display()
        
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        self.download_btn.configure(state="disabled")
        self.status_label.configure(text="Starting download...")
        self.progress_bar.set(0)
        
        # Start download in separate thread
        thread = threading.Thread(target=self.download_video, args=(url,))
        thread.start()
        
    def download_video(self, url):
        try:
            platform = self.platform_var.get()
            quality = self.quality_var.get()
            download_type = self.type_var.get()
            
            if platform == "youtube":
                self.download_youtube(url, quality, download_type)
            else:
                self.download_facebook(url, quality, download_type)
                
        except Exception as e:
            self.window.after(0, lambda: self.status_label.configure(
                text=f"Error: {str(e)}")
            )
            self.window.after(0, lambda: self.download_btn.configure(state="normal"))
            
    def download_youtube(self, url, quality, download_type):
        try:
            yt = YouTube(url)
            yt.register_on_progress_callback(self.update_progress)
            
            if download_type == "video":
                if quality == "highest":
                    stream = yt.streams.get_highest_resolution()
                elif quality == "lowest":
                    stream = yt.streams.get_lowest_resolution()
                else:
                    stream = yt.streams.filter(res=quality).first()
            else:
                stream = yt.streams.get_audio_only()
            
            # Create downloads directory if it doesn't exist
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            
            # Download the video
            filename = stream.download("downloads")
            
            # Add to download history
            self.add_to_history({
                "title": yt.title,
                "url": url,
                "platform": "YouTube",
                "quality": quality,
                "type": download_type,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.window.after(0, lambda: self.status_label.configure(
                text="Download completed successfully!")
            )
            
        except Exception as e:
            raise Exception(f"YouTube download error: {str(e)}")
        finally:
            self.window.after(0, lambda: self.download_btn.configure(state="normal"))
            
    def download_facebook(self, url, quality, download_type):
        try:
            # Note: Facebook video downloading requires additional implementation
            # due to Facebook's security measures
            self.window.after(0, lambda: self.status_label.configure(
                text="Facebook download not implemented yet")
            )
        except Exception as e:
            raise Exception(f"Facebook download error: {str(e)}")
        finally:
            self.window.after(0, lambda: self.download_btn.configure(state="normal"))
            
    def update_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        
        self.window.after(0, lambda: self.progress_bar.set(percentage / 100))
        self.window.after(0, lambda: self.status_label.configure(
            text=f"Downloading... {percentage:.1f}%")
        )
        
    def add_to_history(self, download_info):
        self.download_history.append(download_info)
        self.save_download_history()
        self.update_history_display()
        
    def load_download_history(self):
        try:
            if os.path.exists("download_history.json"):
                with open("download_history.json", "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return []
        
    def save_download_history(self):
        with open("download_history.json", "w") as f:
            json.dump(self.download_history, f)
            
    def update_history_display(self):
        self.history_textbox.delete("1.0", "end")
        for download in reversed(self.download_history):
            self.history_textbox.insert("end", 
                f"Title: {download['title']}\n"
                f"Platform: {download['platform']}\n"
                f"Quality: {download['quality']}\n"
                f"Type: {download['type']}\n"
                f"Date: {download['date']}\n"
                f"{'='*50}\n"
            )
            
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = VideoDownloaderGUI()
    app.run()
