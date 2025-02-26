# pip install customtkinter pyperclip

import customtkinter as ctk
import random
import string
import pyperclip
from tkinter import messagebox
import re

class PasswordGenerator(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Password Generator")
        self.geometry("500x580")
        self.resizable(True, True)
        
        # Set appearance
        ctk.set_appearance_mode("system")  # Use system theme
        ctk.set_default_color_theme("blue")
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Create frame for all widgets
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="Password Generator", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Password length frame
        self.length_frame = ctk.CTkFrame(self.main_frame)
        self.length_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.length_frame.grid_columnconfigure(1, weight=1)
        
        self.length_label = ctk.CTkLabel(
            self.length_frame, 
            text="Password Length:", 
            font=ctk.CTkFont(size=16)
        )
        self.length_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Fixed: Use a DoubleVar instead of StringVar for the slider
        self.length_value = ctk.DoubleVar(value=12)
        self.length_slider = ctk.CTkSlider(
            self.length_frame, 
            from_=4, 
            to=32, 
            number_of_steps=28,
            command=self.slider_changed,
            variable=self.length_value
        )
        self.length_slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.length_display = ctk.CTkLabel(
            self.length_frame, 
            text="12", 
            font=ctk.CTkFont(size=16, weight="bold"),
            width=30
        )
        self.length_display.grid(row=0, column=2, padx=10, pady=10)
        
        # Character types frame
        self.types_frame = ctk.CTkFrame(self.main_frame)
        self.types_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.types_frame.grid_columnconfigure(0, weight=1)
        
        self.types_label = ctk.CTkLabel(
            self.types_frame, 
            text="Character Types:", 
            font=ctk.CTkFont(size=16)
        )
        self.types_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Character type checkboxes
        self.uppercase_var = ctk.BooleanVar(value=True)
        self.uppercase_check = ctk.CTkCheckBox(
            self.types_frame, 
            text="Uppercase Letters (A-Z)", 
            variable=self.uppercase_var,
            checkbox_width=24,
            checkbox_height=24
        )
        self.uppercase_check.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.lowercase_var = ctk.BooleanVar(value=True)
        self.lowercase_check = ctk.CTkCheckBox(
            self.types_frame, 
            text="Lowercase Letters (a-z)", 
            variable=self.lowercase_var,
            checkbox_width=24,
            checkbox_height=24
        )
        self.lowercase_check.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.numbers_var = ctk.BooleanVar(value=True)
        self.numbers_check = ctk.CTkCheckBox(
            self.types_frame, 
            text="Numbers (0-9)", 
            variable=self.numbers_var,
            checkbox_width=24,
            checkbox_height=24
        )
        self.numbers_check.grid(row=3, column=0, padx=20, pady=5, sticky="w")
        
        self.special_var = ctk.BooleanVar(value=True)
        self.special_check = ctk.CTkCheckBox(
            self.types_frame, 
            text="Special Characters (!@#$%^&*)", 
            variable=self.special_var,
            checkbox_width=24,
            checkbox_height=24
        )
        self.special_check.grid(row=4, column=0, padx=20, pady=(5, 10), sticky="w")
        
        # Generated password frame
        self.password_frame = ctk.CTkFrame(self.main_frame)
        self.password_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.password_frame.grid_columnconfigure(0, weight=1)
        
        self.password_label = ctk.CTkLabel(
            self.password_frame, 
            text="Generated Password:", 
            font=ctk.CTkFont(size=16)
        )
        self.password_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.password_entry = ctk.CTkEntry(
            self.password_frame, 
            font=ctk.CTkFont(size=18),
            height=40
        )
        self.password_entry.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.generate_button = ctk.CTkButton(
            self.button_frame, 
            text="Generate Password", 
            font=ctk.CTkFont(size=16),
            command=self.generate_password,
            height=40
        )
        self.generate_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.copy_button = ctk.CTkButton(
            self.button_frame, 
            text="Copy to Clipboard", 
            font=ctk.CTkFont(size=16),
            command=self.copy_to_clipboard,
            height=40
        )
        self.copy_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Strength indicator frame
        self.strength_frame = ctk.CTkFrame(self.main_frame)
        self.strength_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.strength_frame.grid_columnconfigure(1, weight=1)
        
        self.strength_label = ctk.CTkLabel(
            self.strength_frame, 
            text="Password Strength:", 
            font=ctk.CTkFont(size=16)
        )
        self.strength_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.strength_indicator = ctk.CTkProgressBar(self.strength_frame)
        self.strength_indicator.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.strength_indicator.set(0)
        
        self.strength_text = ctk.CTkLabel(
            self.strength_frame, 
            text="", 
            font=ctk.CTkFont(size=14, weight="bold"),
            width=80
        )
        self.strength_text.grid(row=0, column=2, padx=10, pady=10)
        
        # Generate a password on startup
        self.generate_password()
    
    def slider_changed(self, value):
        """Update the displayed length value when slider changes"""
        length = int(float(value))
        self.length_display.configure(text=str(length))
    
    def generate_password(self):
        """Generate a new password based on user selections"""
        # Get selected options
        length = int(self.length_value.get())  # Fixed: directly convert to int
        use_uppercase = self.uppercase_var.get()
        use_lowercase = self.lowercase_var.get()
        use_numbers = self.numbers_var.get()
        use_special = self.special_var.get()
        
        # Validate that at least one option is selected
        if not any([use_uppercase, use_lowercase, use_numbers, use_special]):
            messagebox.showerror("Error", "Please select at least one character type")
            return
        
        # Create character pool based on selections
        char_pool = ""
        required_chars = []
        
        if use_uppercase:
            char_pool += string.ascii_uppercase
            required_chars.append(random.choice(string.ascii_uppercase))
            
        if use_lowercase:
            char_pool += string.ascii_lowercase
            required_chars.append(random.choice(string.ascii_lowercase))
            
        if use_numbers:
            char_pool += string.digits
            required_chars.append(random.choice(string.digits))
            
        if use_special:
            special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?/~"
            char_pool += special_chars
            required_chars.append(random.choice(special_chars))
        
        # Check if password length is at least as long as required characters
        if length < len(required_chars):
            messagebox.showerror(
                "Error", 
                f"Password length must be at least {len(required_chars)} for the selected options"
            )
            return
        
        # Generate password ensuring all required character types are included
        random.shuffle(required_chars)
        remaining_length = length - len(required_chars)
        
        password_chars = required_chars + [random.choice(char_pool) for _ in range(remaining_length)]
        random.shuffle(password_chars)
        password = ''.join(password_chars)
        
        # Update the password display
        self.password_entry.delete(0, 'end')
        self.password_entry.insert(0, password)
        
        # Update strength indicator
        self.update_strength_indicator(password)
    
    def copy_to_clipboard(self):
        """Copy the generated password to clipboard"""
        password = self.password_entry.get()
        if password:
            pyperclip.copy(password)
            messagebox.showinfo("Success", "Password copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "No password to copy")
    
    def update_strength_indicator(self, password):
        """Update the password strength indicator"""
        # Calculate password strength (0.0 to 1.0)
        strength = 0.0
        
        # Base strength on length (up to 0.3)
        length_strength = min(len(password) / 32, 1.0) * 0.3
        strength += length_strength
        
        # Add strength for character variety (up to 0.4)
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_\-+=\[\]{}|;:,.<>?/~]', password))
        
        char_variety = (has_upper + has_lower + has_digit + has_special) / 4
        strength += char_variety * 0.4
        
        # Add strength for character distribution and entropy (up to 0.3)
        char_set_size = 0
        if has_upper:
            char_set_size += 26
        if has_lower:
            char_set_size += 26
        if has_digit:
            char_set_size += 10
        if has_special:
            char_set_size += 32
        
        # Calculate bits of entropy (simplified)
        entropy = len(password) * (char_set_size / 94)
        entropy_strength = min(entropy / 100, 1.0) * 0.3
        strength += entropy_strength
        
        # Update the progress bar
        self.strength_indicator.set(strength)
        
        # Set the strength text
        if strength < 0.25:
            self.strength_text.configure(text="Weak", text_color="#FF5555")
        elif strength < 0.5:
            self.strength_text.configure(text="Moderate", text_color="#FFAA55")
        elif strength < 0.75:
            self.strength_text.configure(text="Strong", text_color="#55AA55")
        else:
            self.strength_text.configure(text="Very Strong", text_color="#55FF55")

def main():
    app = PasswordGenerator()
    app.mainloop()

if __name__ == "__main__":
    main()
