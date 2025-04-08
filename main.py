import tkinter as tk
from tkinter import ttk, messagebox
import os

# Import application modules
from config import validate_config, SSH_HOST, SSH_PORT, SSH_USER, SSH_PASSWORD, REMOTE_DIR, DB_NAME
from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, THEME
from models import DatabaseManager
from services import SSHClient
from ui import UploadView, BrowseView, center_window

class MainApplication(tk.Tk):
    """Main application window"""
    def __init__(self):
        super().__init__()
        
        # Set up the main window
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Check configuration
        is_valid, error_msg = validate_config()
        if not is_valid:
            messagebox.showerror("Configuration Error", error_msg)
            self.destroy()
            return
        
        # Initialize database
        self.db_manager = DatabaseManager(DB_NAME)
        
        # Initialize SSH client
        self.ssh_client = SSHClient(
            host=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USER,
            password=SSH_PASSWORD,
            remote_dir=REMOTE_DIR
        )
        
        # Set up ttk style
        self._setup_style()
        
        # Create the main container
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self._create_tabs()
        
        # Try to connect to the server and refresh the folder list
        self._init_connection()
    
    def _setup_style(self):
        """Set up ttk styles"""
        style = ttk.Style()
        style.theme_use(THEME)
        
        # Configure common styles
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', font=('Arial', 10))
        style.configure('TLabel', font=('Arial', 11), background='#f0f0f0')
        style.configure('TLabelframe', font=('Arial', 11, 'bold'))
        style.configure('TLabelframe.Label', font=('Arial', 11, 'bold'))
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', font=('Arial', 10), padding=[10, 5])
    
    def _create_tabs(self):
        """Create application tabs"""
        # Upload tab
        self.upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.upload_frame, text="Upload Files")
        
        # Browse tab
        self.browse_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.browse_frame, text="Browse Files")
        
        # Initialize views
        self.upload_view = UploadView(
            self.upload_frame, 
            self.ssh_client, 
            self.db_manager,
            on_refresh_callback=self._on_upload_refresh
        )
        self.upload_view.pack(fill=tk.BOTH, expand=True)
        
        self.browse_view = BrowseView(
            self.browse_frame, 
            self.ssh_client, 
            self.db_manager
        )
        self.browse_view.pack(fill=tk.BOTH, expand=True)
    
    def _init_connection(self):
        """Initialize connection and refresh folder list"""
        # Try to connect
        success, error = self.ssh_client.connect()
        if not success:
            messagebox.showwarning(
                "Connection Warning",
                f"Could not connect to server: {error}\n\nYou can try again later."
            )
            return
        
        # Initial folder refresh
        try:
            folders, error = self.ssh_client.list_folders()
            
            if error:
                messagebox.showwarning(
                    "Warning",
                    f"Could not retrieve folder list: {error}"
                )
                return
            
            # Add folders to database
            self.db_manager.clear_folders()
            
            for folder_name in folders:
                if folder_name:  # Skip empty lines
                    full_path = os.path.join(REMOTE_DIR, folder_name).replace("\\", "/")
                    self.db_manager.add_folder(folder_name, full_path)
        except Exception as e:
            messagebox.showwarning(
                "Warning",
                f"Error refreshing folders: {str(e)}"
            )
    
    def _on_upload_refresh(self):
        """Handle refresh from upload view"""
        # Also refresh the browse view
        self.browse_view._load_folders()
    
    def _on_closing(self):
        """Handle window close event"""
        try:
            # Close SSH connection
            if hasattr(self, 'ssh_client') and self.ssh_client:
                self.ssh_client.close()
            
            # Close database connection
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close()
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.destroy()


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()