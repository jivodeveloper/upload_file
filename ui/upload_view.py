import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
from .components import StatusBar, LogPanel, SearchableCombobox

class UploadView(ttk.Frame):
    """File upload interface"""
    def __init__(self, parent, ssh_client, db_manager, on_refresh_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.ssh_client = ssh_client
        self.db_manager = db_manager
        self.on_refresh_callback = on_refresh_callback
        
        # Create frames
        self._create_folder_frame()
        self._create_upload_frame()
        
        # Log panel
        self.log_panel = LogPanel(self)
        self.log_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Load folders
        self._load_folders()
    
    def _create_folder_frame(self):
        """Create the folder creation frame"""
        folder_frame = ttk.LabelFrame(self, text="Create Remote Folder")
        folder_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Folder name entry
        folder_entry_frame = ttk.Frame(folder_frame)
        folder_entry_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(folder_entry_frame, text="Folder Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.folder_name = tk.StringVar()
        folder_entry = ttk.Entry(folder_entry_frame, textvariable=self.folder_name, width=30)
        folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Create folder button
        create_folder_btn = ttk.Button(folder_entry_frame, text="Create Folder", command=self._create_folder)
        create_folder_btn.grid(row=0, column=2, padx=5, pady=5)
    
    def _create_upload_frame(self):
        """Create the file upload frame"""
        upload_frame = ttk.LabelFrame(self, text="Upload Files")
        upload_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Upload frame components
        upload_entry_frame = ttk.Frame(upload_frame)
        upload_entry_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Target folder selection
        ttk.Label(upload_entry_frame, text="Target Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Frame for combobox and search
        folder_select_frame = ttk.Frame(upload_entry_frame)
        folder_select_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Searchable combobox for folder selection
        self.folder_selector = SearchableCombobox(folder_select_frame)
        self.folder_selector.pack(fill=tk.X, expand=True)
        
        # Refresh folder list button
        refresh_btn = ttk.Button(upload_entry_frame, text="↻", width=3, command=self._refresh_folder_list)
        refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Upload button
        browse_btn = ttk.Button(upload_frame, text="Select File to Upload", command=self._browse_file)
        browse_btn.pack(pady=10)
    
    def _load_folders(self):
        """Load folders from database into the combobox"""
        folders, error = self.db_manager.get_folder_names()
        
        if error:
            self.log_panel.log_message(f"Error loading folders: {error}", "ERROR")
            return
        
        self.folder_selector.set_values(folders)
        
        if folders:
            self.log_panel.log_message(f"Loaded {len(folders)} folders from database")
        else:
            self.log_panel.log_message("No folders found in database")
    
    def _refresh_folder_list(self):
        """Refresh folder list from remote server"""
        self.status_bar.set_status("Refreshing folder list...")
        
        try:
            folders, error = self.ssh_client.list_folders()
            
            if error:
                self.log_panel.log_message(f"Error refreshing folder list: {error}", "ERROR")
                self.status_bar.set_status("Failed to refresh folder list")
                messagebox.showerror("Refresh Error", f"Error refreshing folder list: {error}")
                return
            
            # Clear existing folders
            success, error = self.db_manager.clear_folders()
            if not success:
                self.log_panel.log_message(f"Error clearing folder database: {error}", "ERROR")
            
            # Add each folder to database
            for folder_name in folders:
                if folder_name:  # Skip empty lines
                    full_path = os.path.join(self.ssh_client.remote_dir, folder_name).replace("\\", "/")
                    self.db_manager.add_folder(folder_name, full_path)
            
            # Reload folders in UI
            self._load_folders()
            
            # Call refresh callback if provided
            if self.on_refresh_callback:
                self.on_refresh_callback()
            
            self.status_bar.set_status("Folder list refreshed successfully")
            self.log_panel.log_message("Folder list refreshed successfully")
        except Exception as e:
            self.log_panel.log_message(f"Error refreshing folder list: {str(e)}", "ERROR")
            self.status_bar.set_status("Failed to refresh folder list")
            messagebox.showerror("Refresh Error", f"Error refreshing folder list: {str(e)}")
    
    def _create_folder(self):
        """Create a folder on the remote server"""
        folder_name = self.folder_name.get().strip()
        
        if not folder_name:
            messagebox.showerror("Error", "Please enter a folder name")
            return
        
        # Validate folder name (no special characters except underscore and hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', folder_name):
            messagebox.showerror("Error", "Folder name can only contain letters, numbers, underscore and hyphen")
            return
        
        self.status_bar.set_status(f"Creating folder '{folder_name}'...")
        
        try:
            success, result = self.ssh_client.create_folder(folder_name)
            
            if not success:
                self.log_panel.log_message(f"Failed to create folder: {result}", "ERROR")
                self.status_bar.set_status("Failed to create folder")
                messagebox.showerror("Error", f"Failed to create folder: {result}")
                return
            
            remote_folder_path = result
            
            # Add folder to database
            success, error = self.db_manager.add_folder(folder_name, remote_folder_path)
            if not success:
                self.log_panel.log_message(f"Database error: {error}", "ERROR")
                messagebox.showwarning("Warning", f"Folder created on server but database update failed: {error}")
            
            # Reload folder list
            self._load_folders()
            
            # Set the combobox value to the new folder
            self.folder_selector.set(folder_name)
            
            # Clear the folder name entry for next use
            self.folder_name.set("")
            
            self.status_bar.set_status(f"Folder '{folder_name}' created successfully")
            self.log_panel.log_message(f"Folder created successfully: {remote_folder_path}")
            messagebox.showinfo("Success", f"Folder '{folder_name}' created successfully")
            
            # Call refresh callback if provided
            if self.on_refresh_callback:
                self.on_refresh_callback()
                
        except Exception as e:
            self.log_panel.log_message(f"Error creating folder: {str(e)}", "ERROR")
            self.status_bar.set_status("Failed to create folder")
            messagebox.showerror("Error", f"Error creating folder: {str(e)}")
    
    def _browse_file(self):
        """Browse for file and upload it"""
        target_folder = self.folder_selector.get()
        
        if not target_folder:
            messagebox.showerror("Error", "Please select a target folder")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select a file to upload",
            filetypes=[
                ("All Files", "*.*"),
                ("Text Files", "*.txt"),
                ("PDF Files", "*.pdf"),
                ("Image Files", "*.jpg *.jpeg *.png *.gif"),
                ("Document Files", "*.doc *.docx *.xls *.xlsx *.ppt *.pptx")
            ]
        )
        
        if not file_path:
            return  # User canceled the file selection
        
        self._upload_file(file_path, target_folder)
    
    def _upload_file(self, local_file_path, target_folder):
        """Upload the file to the specified remote folder"""
        self.status_bar.set_status(f"Uploading file to {target_folder}...")
        self.log_panel.log_message(f"Selected file: {local_file_path}")
        
        try:
            result, error = self.ssh_client.upload_file(local_file_path, target_folder)
            
            if error:
                self.log_panel.log_message(f"Error during upload: {error}", "ERROR")
                self.status_bar.set_status("Upload failed")
                messagebox.showerror("Upload Error", f"Error: {error}")
                return
            
            remote_file_path = result["path"]
            file_size = result["size"]
            file_name = os.path.basename(local_file_path)
            
            # Add file to database
            success, error = self.db_manager.add_file(
                file_name, 
                target_folder, 
                local_file_path, 
                remote_file_path,
                file_size
            )
            
            if not success:
                self.log_panel.log_message(f"Database error: {error}", "ERROR")
                messagebox.showwarning("Warning", f"File uploaded but database update failed: {error}")
            
            self.status_bar.set_status("File uploaded successfully")
            self.log_panel.log_message(f"File uploaded successfully to {remote_file_path}")
            messagebox.showinfo("Upload Result", f"File uploaded successfully to {remote_file_path}")
            
            # Call refresh callback if provided
            if self.on_refresh_callback:
                self.on_refresh_callback()
                
        except Exception as e:
            self.log_panel.log_message(f"Error during upload: {str(e)}", "ERROR")
            self.status_bar.set_status("Upload failed")
            messagebox.showerror("Upload Error", f"Error: {str(e)}")