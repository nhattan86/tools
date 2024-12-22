import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import PyPDF2
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import os
import io
import math

class PDFManager:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Manager")
        
        # Make it fullscreen and set minimum size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.state('zoomed')  # Windows fullscreen
        self.root.minsize(1024, 768)
        
        self.root.configure(bg="#f0f0f0")
        
        # Variables
        self.pdf_path = None
        self.pdf_info = {}
        self.selected_pages = set()
        self.page_thumbnails = []
        # Larger thumbnails (maintaining A4 proportion)
        self.thumbnail_size = (250, 354)  # Increased size for Full HD
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Style configuration
        self.setup_styles()
        
        # Create sections
        self.create_upload_section()
        self.create_info_section()
        self.create_thumbnails_section()
        self.create_save_section()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('TButton', padding=5, font=('Arial', 10))
        style.configure('TLabel', padding=5, font=('Arial', 10))
        style.configure('Header.TLabel', padding=5, font=('Arial', 12, 'bold'))
        style.configure('Big.TButton', padding=10, font=('Arial', 11, 'bold'))

    def create_upload_section(self):
        upload_frame = ttk.LabelFrame(self.main_frame, text="Upload PDF", padding="10")
        upload_frame.pack(fill=tk.X, pady=5)
        
        self.file_label = ttk.Label(upload_frame, text="No file selected", style='Header.TLabel')
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        upload_btn = ttk.Button(upload_frame, text="Browse", command=self.upload_pdf, style='Big.TButton')
        upload_btn.pack(side=tk.RIGHT, padx=10)

    def create_info_section(self):
        info_frame = ttk.LabelFrame(self.main_frame, text="PDF Information", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        # Create a sub-frame for better organization
        info_sub_frame = ttk.Frame(info_frame)
        info_sub_frame.pack(fill=tk.X)
        
        # Size info
        size_frame = ttk.Frame(info_sub_frame)
        size_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(size_frame, text="Size:", style='Header.TLabel').pack(side=tk.LEFT)
        self.size_label = ttk.Label(size_frame, text="-")
        self.size_label.pack(side=tk.LEFT, padx=5)
        
        # Pages info
        pages_frame = ttk.Frame(info_sub_frame)
        pages_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(pages_frame, text="Total Pages:", style='Header.TLabel').pack(side=tk.LEFT)
        self.pages_label = ttk.Label(pages_frame, text="-")
        self.pages_label.pack(side=tk.LEFT, padx=5)
        
        # Selection info
        selection_frame = ttk.Frame(info_sub_frame)
        selection_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(selection_frame, text="Selected:", style='Header.TLabel').pack(side=tk.LEFT)
        self.selection_label = ttk.Label(selection_frame, text="0 pages")
        self.selection_label.pack(side=tk.LEFT, padx=5)

    def create_thumbnails_section(self):
        self.canvas_frame = ttk.LabelFrame(self.main_frame, text="PDF Pages (Click to select)", padding="10")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        scrollbar_y = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Grid layout
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create frame inside canvas for thumbnails
        self.thumbnails_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.thumbnails_frame, anchor='nw')
        
        # Bind mouse wheel and frame configuration
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.thumbnails_frame.bind('<Configure>', self._on_frame_configure)
        
        # Bind canvas resize
        self.canvas.bind('<Configure>', self._on_canvas_resize)

    def create_save_section(self):
        save_frame = ttk.LabelFrame(self.main_frame, text="Save Options", padding="10")
        save_frame.pack(fill=tk.X, pady=5)
        
        # Create a sub-frame for better organization
        save_sub_frame = ttk.Frame(save_frame)
        save_sub_frame.pack(fill=tk.X, expand=True)
        
        # Filename section
        filename_frame = ttk.Frame(save_sub_frame)
        filename_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(filename_frame, text="New filename:", style='Header.TLabel').pack(side=tk.LEFT, padx=5)
        self.save_name = ttk.Entry(filename_frame, font=('Arial', 11))
        self.save_name.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Buttons section
        buttons_frame = ttk.Frame(save_sub_frame)
        buttons_frame.pack(side=tk.RIGHT, padx=10)
        
        select_all_btn = ttk.Button(buttons_frame, text="Select All", 
                                  command=self.select_all_pages, style='Big.TButton')
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(buttons_frame, text="Clear Selection", 
                             command=self.clear_selection, style='Big.TButton')
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = ttk.Button(buttons_frame, text="Save Selected Pages", 
                            command=self.save_pdf, style='Big.TButton')
        save_btn.pack(side=tk.LEFT, padx=5)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        # Calculate number of columns based on canvas width
        canvas_width = event.width
        thumb_width = self.thumbnail_size[0] + 20  # Add padding
        self.columns = max(1, canvas_width // thumb_width)
        if hasattr(self, 'pdf_path') and self.pdf_path:
            self.load_thumbnails()

    def load_thumbnails(self):
        # Clear existing thumbnails
        for widget in self.thumbnails_frame.winfo_children():
            widget.destroy()
        self.page_thumbnails.clear()
        
        try:
            doc = fitz.open(self.pdf_path)
            current_row = 0
            current_col = 0
            
            for page_num in range(len(doc)):
                # Get page and create pixmap
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # Increased zoom factor
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.thumbnail(self.thumbnail_size)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)
                self.page_thumbnails.append(photo)
                
                # Create thumbnail frame
                thumb_frame = ttk.Frame(self.thumbnails_frame)
                thumb_frame.grid(row=current_row, column=current_col, padx=10, pady=10)
                
                # Create thumbnail label
                label = tk.Label(thumb_frame, image=photo, bd=2, relief='solid')
                label.pack()
                
                # Create page number label
                page_label = ttk.Label(thumb_frame, text=f"Page {page_num + 1}", 
                                     font=('Arial', 10, 'bold'))
                page_label.pack()
                
                # Bind events
                label.bind('<Button-1>', lambda e, pn=page_num+1: self.toggle_page_selection(pn))
                label.bind('<Shift-Button-1>', lambda e, pn=page_num+1: self.shift_select_page(pn))
                label.page_num = page_num + 1
                
                # Update grid position
                current_col += 1
                if current_col >= self.columns:
                    current_col = 0
                    current_row += 1
            
            doc.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading thumbnails: {str(e)}")

    def upload_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.pdf_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.selected_pages.clear()
            self.update_pdf_info()
            self.load_thumbnails()

    def update_pdf_info(self):
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                size = os.path.getsize(self.pdf_path) / 1024  # Size in KB
                num_pages = len(pdf.pages)
                
                self.size_label.config(text=f"Size: {size:.2f} KB")
                self.pages_label.config(text=f"Pages: {num_pages}")
                
                self.pdf_info = {
                    'size': size,
                    'pages': num_pages
                }
        except Exception as e:
            messagebox.showerror("Error", f"Error reading PDF: {str(e)}")

    

    def toggle_page_selection(self, page_num):
        if page_num in self.selected_pages:
            self.selected_pages.remove(page_num)
        else:
            self.selected_pages.add(page_num)
        self.update_selection_visual()

    def shift_select_page(self, page_num):
        if not self.selected_pages:
            self.selected_pages.add(page_num)
        else:
            last_selected = max(self.selected_pages)
            start = min(last_selected, page_num)
            end = max(last_selected, page_num)
            self.selected_pages.update(range(start, end + 1))
        self.update_selection_visual()

    def update_selection_visual(self):
        # Update all thumbnail borders
        for widget in self.thumbnails_frame.winfo_children():
            label = widget.winfo_children()[0]  # Get the thumbnail label
            if hasattr(label, 'page_num'):
                if label.page_num in self.selected_pages:
                    label.configure(bd=4, relief='solid', bg='lightblue')
                else:
                    label.configure(bd=2, relief='solid', bg='SystemButtonFace')
        
        # Update selection counter
        self.selection_label.config(text=f"Selected: {len(self.selected_pages)} pages")

    def select_all_pages(self):
        self.selected_pages = set(range(1, self.pdf_info['pages'] + 1))
        self.update_selection_visual()

    def clear_selection(self):
        self.selected_pages.clear()
        self.update_selection_visual()

    def save_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("Warning", "Please upload a PDF first!")
            return
            
        if not self.selected_pages:
            messagebox.showwarning("Warning", "Please select at least one page!")
            return
            
        new_filename = self.save_name.get()
        if not new_filename:
            messagebox.showwarning("Warning", "Please enter a filename!")
            return
            
        if not new_filename.endswith('.pdf'):
            new_filename += '.pdf'
            
        try:
            # Create new PDF
            with open(self.pdf_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Add selected pages to new PDF
                for page_num in sorted(self.selected_pages):
                    pdf_writer.add_page(pdf.pages[page_num - 1])  # Convert to 0-based index
                
                # Save the new PDF
                with open(new_filename, 'wb') as output_file:
                    pdf_writer.write(output_file)
            
            messagebox.showinfo("Success", f"PDF saved as {new_filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving PDF: {str(e)}")

def main():
    root = tk.Tk()
    app = PDFManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
