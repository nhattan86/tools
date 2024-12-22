import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import PyPDF2
import os

class PDFManager:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Manager")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Variables
        self.pdf_path = None
        self.pdf_info = {}
        self.selected_pages = set()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Style configuration
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TLabel', padding=5)
        
        # Create sections
        self.create_upload_section()
        self.create_info_section()
        self.create_page_selection_section()
        self.create_save_section()

    def create_upload_section(self):
        upload_frame = ttk.LabelFrame(self.main_frame, text="Upload PDF", padding="5")
        upload_frame.pack(fill=tk.X, pady=5)
        
        self.file_label = ttk.Label(upload_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        upload_btn = ttk.Button(upload_frame, text="Browse", command=self.upload_pdf)
        upload_btn.pack(side=tk.RIGHT, padx=5)

    def create_info_section(self):
        info_frame = ttk.LabelFrame(self.main_frame, text="PDF Information", padding="5")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.size_label = ttk.Label(info_frame, text="Size: -")
        self.size_label.pack(anchor=tk.W)
        
        self.pages_label = ttk.Label(info_frame, text="Pages: -")
        self.pages_label.pack(anchor=tk.W)

    def create_page_selection_section(self):
        selection_frame = ttk.LabelFrame(self.main_frame, text="Page Selection", padding="5")
        selection_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create left frame for page selection methods
        left_frame = ttk.Frame(selection_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Single page entry
        single_frame = ttk.Frame(left_frame)
        single_frame.pack(fill=tk.X, pady=5)
        ttk.Label(single_frame, text="Add single page:").pack(side=tk.LEFT)
        self.single_page = ttk.Entry(single_frame, width=5)
        self.single_page.pack(side=tk.LEFT, padx=5)
        ttk.Button(single_frame, text="Add", command=self.add_single_page).pack(side=tk.LEFT)
        
        # Range entry
        range_frame = ttk.Frame(left_frame)
        range_frame.pack(fill=tk.X, pady=5)
        ttk.Label(range_frame, text="Add range:").pack(side=tk.LEFT)
        self.range_start = ttk.Entry(range_frame, width=5)
        self.range_start.pack(side=tk.LEFT, padx=5)
        ttk.Label(range_frame, text="to").pack(side=tk.LEFT)
        self.range_end = ttk.Entry(range_frame, width=5)
        self.range_end.pack(side=tk.LEFT, padx=5)
        ttk.Button(range_frame, text="Add", command=self.add_page_range).pack(side=tk.LEFT)
        
        # Create right frame for selected pages display
        right_frame = ttk.Frame(selection_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Selected pages list
        ttk.Label(right_frame, text="Selected Pages:").pack(anchor=tk.W)
        self.pages_listbox = tk.Listbox(right_frame, selectmode=tk.MULTIPLE)
        self.pages_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Buttons for listbox
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_pages).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_pages).pack(side=tk.LEFT)

    def create_save_section(self):
        save_frame = ttk.LabelFrame(self.main_frame, text="Save PDF", padding="5")
        save_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(save_frame, text="New filename:").pack(side=tk.LEFT, padx=5)
        self.save_name = ttk.Entry(save_frame)
        self.save_name.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        save_btn = ttk.Button(save_frame, text="Save", command=self.save_pdf)
        save_btn.pack(side=tk.RIGHT, padx=5)

    def upload_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.pdf_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.update_pdf_info()
            self.clear_pages()

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

    def add_single_page(self):
        try:
            page = int(self.single_page.get())
            if self.validate_page_number(page):
                self.add_pages([page])
                self.single_page.delete(0, tk.END)
        except ValueError:
            messagebox.showwarning("Warning", "Please enter a valid page number!")

    def add_page_range(self):
        try:
            start = int(self.range_start.get())
            end = int(self.range_end.get())
            
            if start > end:
                messagebox.showwarning("Warning", "Start page must be less than end page!")
                return
                
            valid_pages = []
            for page in range(start, end + 1):
                if self.validate_page_number(page):
                    valid_pages.append(page)
                    
            self.add_pages(valid_pages)
            self.range_start.delete(0, tk.END)
            self.range_end.delete(0, tk.END)
            
        except ValueError:
            messagebox.showwarning("Warning", "Please enter valid page numbers!")

    def validate_page_number(self, page):
        if not self.pdf_path:
            messagebox.showwarning("Warning", "Please upload a PDF first!")
            return False
        
        if page < 1 or page > self.pdf_info['pages']:
            messagebox.showwarning("Warning", f"Page number must be between 1 and {self.pdf_info['pages']}!")
            return False
            
        return True

    def add_pages(self, pages):
        for page in pages:
            if page not in self.selected_pages:
                self.selected_pages.add(page)
        self.update_pages_listbox()

    def remove_selected_pages(self):
        selected_indices = self.pages_listbox.curselection()
        pages_to_remove = [int(self.pages_listbox.get(i).split()[1]) for i in selected_indices]
        
        for page in pages_to_remove:
            self.selected_pages.discard(page)
            
        self.update_pages_listbox()

    def clear_pages(self):
        self.selected_pages.clear()
        self.update_pages_listbox()

    def update_pages_listbox(self):
        self.pages_listbox.delete(0, tk.END)
        for page in sorted(self.selected_pages):
            self.pages_listbox.insert(tk.END, f"Page {page}")

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
