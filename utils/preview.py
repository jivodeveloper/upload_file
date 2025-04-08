import os
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import mimetypes
import webbrowser

class FilePreviewWindow(tk.Toplevel):
    """Window for previewing files"""
    def __init__(self, parent, title, file_path=None, file_content=None, file_type=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.title(title)
        self.geometry("800x600")
        self.minsize(400, 300)
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initialize preview
        if file_path:
            self.preview_file(file_path, file_type)
        elif file_content:
            self.preview_content(file_content, file_type)
        else:
            self.show_error("No file or content provided for preview")
    
    def preview_file(self, file_path, file_type=None):
        """Preview a file based on its type"""
        if not os.path.exists(file_path):
            self.show_error(f"File not found: {file_path}")
            return
        
        # Determine file type if not provided
        if not file_type:
            file_type = get_file_type(file_path)
        
        # Handle different file types
        if file_type == "image":
            self.preview_image(file_path)
        elif file_type == "text":
            self.preview_text_file(file_path)
        elif file_type == "pdf":
            self.preview_pdf(file_path)
        elif file_type == "html":
            self.preview_html(file_path)
        else:
            self.show_unsupported(file_path, file_type)
    
    def preview_content(self, content, file_type):
        """Preview content based on its type"""
        if file_type == "image" and isinstance(content, bytes):
            self.preview_image_data(content)
        elif file_type == "text" and isinstance(content, str):
            self.preview_text(content)
        else:
            self.show_error("Unsupported content type for preview")
    
    def preview_image(self, image_path):
        """Display an image for preview"""
        try:
            # Create a frame for the image
            image_frame = ttk.Frame(self.main_frame)
            image_frame.pack(fill=tk.BOTH, expand=True)
            
            # Open and resize image
            img = Image.open(image_path)
            self.display_image(img, image_frame)
            
        except Exception as e:
            self.show_error(f"Error previewing image: {str(e)}")
    
    def preview_image_data(self, image_data):
        """Display image from binary data"""
        try:
            # Create a frame for the image
            image_frame = ttk.Frame(self.main_frame)
            image_frame.pack(fill=tk.BOTH, expand=True)
            
            # Open image from bytes
            img = Image.open(io.BytesIO(image_data))
            self.display_image(img, image_frame)
            
        except Exception as e:
            self.show_error(f"Error previewing image data: {str(e)}")
    
    def display_image(self, img, frame):
        """Display an image with scrollbars if needed"""
        # Calculate aspect ratio and resize if necessary
        max_width = 780  # Slightly less than window width
        max_height = 550  # Slightly less than window height
        
        # Get original dimensions
        width, height = img.size
        
        # Resize if the image is larger than the window
        if width > max_width or height > max_height:
            # Calculate aspect ratio
            aspect_ratio = width / height
            
            if width > max_width:
                width = max_width
                height = int(width / aspect_ratio)
            
            if height > max_height:
                height = max_height
                width = int(height * aspect_ratio)
            
            img = img.resize((width, height), Image.LANCZOS)
        
        # Create canvas with scrollbars for the image
        canvas = tk.Canvas(frame, width=min(width, max_width), height=min(height, max_height))
        
        # Add scrollbars if needed
        h_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
        v_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        
        # Configure canvas scrolling
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Pack scrollbars and canvas
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Set canvas scroll region
        canvas.configure(scrollregion=(0, 0, width, height))
        
        # Convert image to PhotoImage and display
        self.tk_image = ImageTk.PhotoImage(img)
        canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
    
    def preview_text_file(self, text_file_path):
        """Display text file content"""
        try:
            with open(text_file_path, 'r', encoding='utf-8', errors='replace') as f:
                text_content = f.read()
            
            self.preview_text(text_content)
        except Exception as e:
            self.show_error(f"Error reading text file: {str(e)}")
    
    def preview_text(self, text_content):
        """Display text content"""
        # Create text widget
        text_frame = ttk.Frame(self.main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add text widget with scrollbars
        text_widget = tk.Text(text_frame, wrap=tk.WORD, padx=5, pady=5)
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        
        text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert text content
        text_widget.insert(tk.END, text_content)
        text_widget.config(state=tk.DISABLED)  # Make read-only
    
    def preview_pdf(self, pdf_path):
        """Preview PDF file using system default if possible, otherwise show message"""
        try:
            # Attempt to open with system default PDF viewer
            if platform.system() == "Windows":
                os.startfile(pdf_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", pdf_path])
            else:  # Linux
                subprocess.call(["xdg-open", pdf_path])
            
            # Show message in window
            message = (
                f"PDF file is being opened in your default PDF viewer.\n\n"
                f"File: {os.path.basename(pdf_path)}\n"
                f"If the PDF did not open automatically, please check your system's default PDF viewer settings."
            )
            self.show_message(message)
            
        except Exception as e:
            self.show_error(f"Error opening PDF: {str(e)}")
    
    def preview_html(self, html_path):
        """Preview HTML file in system browser"""
        try:
            # Convert to file URL
            file_url = f"file://{os.path.abspath(html_path)}"
            
            # Open in default web browser
            webbrowser.open(file_url)
            
            # Show message in window
            message = (
                f"HTML file is being opened in your default web browser.\n\n"
                f"File: {os.path.basename(html_path)}\n"
                f"If the browser did not open automatically, please check your system settings."
            )
            self.show_message(message)
            
        except Exception as e:
            self.show_error(f"Error opening HTML: {str(e)}")
    
    def show_message(self, message):
        """Display a message"""
        message_frame = ttk.Frame(self.main_frame)
        message_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            message_frame, 
            text=message,
            justify=tk.LEFT,
            wraplength=780
        ).pack(pady=20)
    
    def show_error(self, error_message):
        """Display an error message"""
        error_frame = ttk.Frame(self.main_frame)
        error_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            error_frame, 
            text=error_message,
            foreground="red",
            justify=tk.LEFT,
            wraplength=780
        ).pack(pady=20)
    
    def show_unsupported(self, file_path, file_type):
        """Show message for unsupported file types"""
        message = (
            f"Preview not available for this file type: {file_type}\n\n"
            f"File: {os.path.basename(file_path)}"
        )
        self.show_message(message)


def get_file_type(file_path):
    """Determine file type based on extension"""
    ext = os.path.splitext(file_path)[1].lower()
    
    # Images
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
        return "image"
    
    # Text files
    if ext in ['.txt', '.log', '.csv', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.ini', '.cfg']:
        return "text"
    
    # PDF
    if ext == '.pdf':
        return "pdf"
    
    # HTML
    if ext in ['.html', '.htm']:
        return "html"
    
    # Office documents - these can't be previewed directly, but we can identify them
    if ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        return "office"
    
    # Return the mime type as fallback
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        main_type = mime_type.split('/')[0]
        return main_type
    
    return "unknown"


def preview_file(parent, file_path, title=None):
    """Open a preview window for a file"""
    if not title:
        title = f"Preview: {os.path.basename(file_path)}"
    
    return FilePreviewWindow(parent, title, file_path=file_path)