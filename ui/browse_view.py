import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
from .components import StatusBar, LogPanel, SearchableCombobox, FileListView, format_file_size
from utils import preview_file

class BrowseView(ttk.Frame):
    """File browsing and download interface"""
    def __init__(self, parent, ssh_client, db_manager, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.ssh_client = ssh_client
        self.db_manager = db_manager
        self.current_folder = None
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
        
        # Ensure temp directory exists
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # Main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create folder selection frame
        self._create_folder_selection_frame()
        
        # Create file list frame
        self._create_file_list_frame()
        
        # Action buttons
        self._create_action_buttons()
        
        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Load folders
        self._load_folders()
    
    def _create_folder_selection_frame(self):
        """Create folder selection section"""
        folder_frame = ttk.LabelFrame(self.main_container, text="Remote Folders")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        folder_selection_frame = ttk.Frame(folder_frame)
        folder_selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Folder label
        ttk.Label(folder_selection_frame, text="Select Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Searchable combobox for folder selection
        self.folder_selector = SearchableCombobox(folder_selection_frame)
        self.folder_selector.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Bind selection event
        self.folder_selector.combobox.bind("<<ComboboxSelected>>", self._on_folder_selected)
        
        # Refresh button
        refresh_btn = ttk.Button(folder_selection_frame, text="↻", width=3, command=self.refresh_folder_list)
        refresh_btn.grid(row=0, column=2, padx=5, pady=5)
    
    def _create_file_list_frame(self):
        """Create file list section"""
        file_frame = ttk.LabelFrame(self.main_container, text="Files")
        file_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create file list view with custom columns
        columns = [
            {"id": "name", "text": "File Name", "width": 250},
            {"id": "size", "text": "Size", "width": 100},
            {"id": "date", "text": "Upload Date", "width": 150}
        ]
        self.file_list = FileListView(file_frame, columns=columns)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind double-click event for file download
        self.file_list.bind_double_click(self._on_file_double_click)
        
        # Bind selection event to enable/disable buttons
        self.file_list.tree.bind("<<TreeviewSelect>>", self._on_file_selected)
    
    def _create_action_buttons(self):
        """Create action buttons"""
        action_frame = ttk.Frame(self.main_container)
        action_frame.pack(fill=tk.X, pady=10)
        
        # Preview button
        self.preview_btn = ttk.Button(
            action_frame, 
            text="Preview File",
            command=self._preview_selected_file,
            state=tk.DISABLED
        )
        self.preview_btn.pack(side=tk.RIGHT, padx=5)
        
        # Download button
        self.download_btn = ttk.Button(
            action_frame, 
            text="Download Selected",
            command=self._download_selected_file,
            state=tk.DISABLED
        )
        self.download_btn.pack(side=tk.RIGHT, padx=5)
        
        # Delete button
        self.delete_btn = ttk.Button(
            action_frame, 
            text="Delete Selected",
            command=self._delete_selected_file,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        
        # Refresh files button
        self.refresh_files_btn = ttk.Button(
            action_frame, 
            text="Refresh Files",
            command=self._refresh_files,
            state=tk.DISABLED
        )
        self.refresh_files_btn.pack(side=tk.LEFT, padx=5)
    
    def _load_folders(self):
        """Load folders from database into the combobox"""
        folders, error = self.db_manager.get_folder_names()
        
        if error:
            self.status_bar.set_status(f"Error: {error}")
            messagebox.showerror("Database Error", f"Error loading folders: {error}")
            return
        
        self.folder_selector.set_values(folders)
        
        if folders:
            self.status_bar.set_status(f"Loaded {len(folders)} folders")
        else:
            self.status_bar.set_status("No folders found")
    
    def refresh_folder_list(self):
        """Refresh folder list from remote server"""
        self.status_bar.set_status("Refreshing folder list...")
        
        try:
            folders, error = self.ssh_client.list_folders()
            
            if error:
                self.status_bar.set_status(f"Error: {error}")
                messagebox.showerror("Refresh Error", f"Error refreshing folder list: {error}")
                return
            
            # Clear existing folders
            success, error = self.db_manager.clear_folders()
            if not success:
                self.status_bar.set_status(f"Error: {error}")
                messagebox.showerror("Database Error", f"Error clearing folder database: {error}")
                return
            
            # Add each folder to database
            for folder_name in folders:
                if folder_name:  # Skip empty lines
                    full_path = os.path.join(self.ssh_client.remote_dir, folder_name).replace("\\", "/")
                    self.db_manager.add_folder(folder_name, full_path)
            
            # Reload folders in UI
            self._load_folders()
            
            # Clear file list
            self.file_list.populate([])
            self._disable_file_buttons()
            
            self.status_bar.set_status("Folder list refreshed successfully")
        except Exception as e:
            self.status_bar.set_status(f"Error: {str(e)}")
            messagebox.showerror("Refresh Error", f"Error refreshing folder list: {str(e)}")
    
    def _on_folder_selected(self, event=None):
        """Handle folder selection"""
        selected_folder = self.folder_selector.get()
        if not selected_folder:
            return
        
        self.current_folder = selected_folder
        self._load_files_in_folder(selected_folder)
        self._enable_refresh_button()
    
    def _on_file_selected(self, event=None):
        """Handle file selection in the list"""
        selected_item = self.file_list.get_selected_item()
        if selected_item:
            self._enable_file_buttons()
        else:
            self._disable_file_buttons()
    
    def _load_files_in_folder(self, folder_name):
        """Load files from selected folder"""
        self.status_bar.set_status(f"Loading files in folder '{folder_name}'...")
        
        try:
            # Get files from remote server
            files, error = self.ssh_client.list_files(folder_name)
            
            if error:
                self.status_bar.set_status(f"Error: {error}")
                messagebox.showerror("Error", f"Error listing files: {error}")
                return
            
            # Prepare list items
            list_items = []
            for file_name in files:
                if not file_name:  # Skip empty names
                    continue
                
                # Get file info from database or server
                file_record, _ = self.db_manager.get_file_by_name(folder_name, file_name)
                
                if file_record:
                    # Use database info
                    file_id, local_path, remote_path, size = file_record
                    # Format for display
                    size_formatted = format_file_size(size)
                    date = datetime.now().strftime("%Y-%m-%d %H:%M")  # Use placeholder date for now
                else:
                    # Get info from server
                    file_info, err = self.ssh_client.get_file_info(folder_name, file_name)
                    if file_info:
                        size = file_info.get("size", 0)
                        size_formatted = format_file_size(size)
                        date = datetime.fromtimestamp(file_info.get("mtime", 0)).strftime("%Y-%m-%d %H:%M")
                    else:
                        size_formatted = "Unknown"
                        date = "Unknown"
                
                # Add to display list
                list_items.append((file_name, size_formatted, date))
            
            # Populate the list view
            self.file_list.populate(list_items)
            
            self.status_bar.set_status(f"Loaded {len(list_items)} files from '{folder_name}'")
        except Exception as e:
            self.status_bar.set_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error loading files: {str(e)}")
    
    def _on_file_double_click(self, event):
        """Handle double-click on file"""
        self._preview_selected_file()
    
    def _preview_selected_file(self):
        """Preview the selected file"""
        if not self.current_folder:
            messagebox.showerror("Error", "No folder selected")
            return
        
        selected_item = self.file_list.get_selected_item()
        if not selected_item:
            messagebox.showerror("Error", "No file selected")
            return
        
        file_name = selected_item[0]
        
        self.status_bar.set_status(f"Preparing preview for {file_name}...")
        
        try:
            # Check if file exists in database
            file_record, _ = self.db_manager.get_file_by_name(self.current_folder, file_name)
            
            local_path = None
            if file_record:
                # File exists in database, check if local path exists
                _, local_path, _, _ = file_record
                if local_path and os.path.exists(local_path):
                    # Use existing local file
                    self.status_bar.set_status(f"Previewing {file_name}")
                    preview_file(self, local_path)
                    return
            
            # File doesn't exist locally or local copy not found, download to temp directory
            temp_file_path = os.path.join(self.temp_dir, file_name)
            
            # Download the file
            result, error = self.ssh_client.download_file(
                self.current_folder, 
                file_name, 
                self.temp_dir
            )
            
            if error:
                self.status_bar.set_status(f"Error: {error}")
                messagebox.showerror("Preview Error", f"Error downloading file for preview: {error}")
                return
            
            # Update database with local path if needed
            if not file_record:
                # Get file info from server
                file_info, _ = self.ssh_client.get_file_info(self.current_folder, file_name)
                if file_info:
                    size = file_info.get("size", 0)
                    remote_path = os.path.join(
                        self.ssh_client.remote_dir, 
                        self.current_folder, 
                        file_name
                    ).replace("\\", "/")
                    
                    # Add to database with temp path
                    self.db_manager.add_file(
                        file_name,
                        self.current_folder,
                        temp_file_path,
                        remote_path,
                        size
                    )
            
            # Show preview
            self.status_bar.set_status(f"Previewing {file_name}")
            preview_file(self, temp_file_path)
            
        except Exception as e:
            self.status_bar.set_status(f"Error: {str(e)}")
            messagebox.showerror("Preview Error", f"Error: {str(e)}")
    
    def _download_selected_file(self):
        """Download the selected file"""
        if not self.current_folder:
            messagebox.showerror("Error", "No folder selected")
            return
        
        selected_item = self.file_list.get_selected_item()
        if not selected_item:
            messagebox.showerror("Error", "No file selected")
            return
        
        file_name = selected_item[0]
        
        # Ask for download location
        download_dir = filedialog.askdirectory(title="Select Download Location")
        if not download_dir:
            return  # User canceled
        
        self.status_bar.set_status(f"Downloading {file_name}...")
        
        try:
            result, error = self.ssh_client.download_file(
                self.current_folder, 
                file_name, 
                download_dir
            )
            
            if error:
                self.status_bar.set_status(f"Error: {error}")
                messagebox.showerror("Download Error", f"Error downloading file: {error}")
                return
            
            local_path = result["path"]
            
            # Update database with local path if needed
            file_record, _ = self.db_manager.get_file_by_name(self.current_folder, file_name)
            if not file_record:
                # Get file info from server
                file_info, _ = self.ssh_client.get_file_info(self.current_folder, file_name)
                if file_info:
                    size = file_info.get("size", 0)
                    remote_path = os.path.join(
                        self.ssh_client.remote_dir, 
                        self.current_folder, 
                        file_name
                    ).replace("\\", "/")
                    
                    # Add to database
                    self.db_manager.add_file(
                        file_name,
                        self.current_folder,
                        local_path,
                        remote_path,
                        size
                    )
            
            self.status_bar.set_status(f"File downloaded to {local_path}")
            messagebox.showinfo("Download Complete", f"File downloaded to:\n{local_path}")
        except Exception as e:
            self.status_bar.set_status(f"Error: {str(e)}")
            messagebox.showerror("Download Error", f"Error: {str(e)}")
    
    def _delete_selected_file(self):
        """Delete the selected file"""
        if not self.current_folder:
            messagebox.showerror("Error", "No folder selected")
            return
        
        selected_item = self.file_list.get_selected_item()
        if not selected_item:
            messagebox.showerror("Error", "No file selected")
            return
        
        file_name = selected_item[0]
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete '{file_name}'?"
        )
        if not confirm:
            return
        
        self.status_bar.set_status(f"Deleting {file_name}...")
        
        try:
            success, error = self.ssh_client.delete_file(self.current_folder, file_name)
            
            if not success:
                self.status_bar.set_status(f"Error: {error}")
                messagebox.showerror("Delete Error", f"Error deleting file: {error}")
                return
            
            # Remove from database if exists
            file_record, _ = self.db_manager.get_file_by_name(self.current_folder, file_name)
            if file_record:
                file_id = file_record[0]
                self.db_manager.delete_file(file_id)
            
            # Refresh file list
            self._load_files_in_folder(self.current_folder)
            
            self.status_bar.set_status(f"File '{file_name}' deleted successfully")
            messagebox.showinfo("Delete Complete", f"File '{file_name}' deleted successfully")
        except Exception as e:
            self.status_bar.set_status(f"Error: {str(e)}")
            messagebox.showerror("Delete Error", f"Error: {str(e)}")
    
    def _refresh_files(self):
        """Refresh the file list for current folder"""
        if not self.current_folder:
            return
        
        self._load_files_in_folder(self.current_folder)
    
    def _enable_file_buttons(self):
        """Enable file action buttons"""
        self.download_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        self.preview_btn.config(state=tk.NORMAL)
    
    def _disable_file_buttons(self):
        """Disable file action buttons"""
        self.download_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.DISABLED)
    
    def _enable_refresh_button(self):
        """Enable refresh files button"""
        self.refresh_files_btn.config(state=tk.NORMAL)
    
    def select_folder(self, folder_name):
        """Programmatically select a folder"""
        if folder_name in self.folder_selector.all_values:
            self.folder_selector.set(folder_name)
            self._on_folder_selected()