import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import os
from datetime import datetime

class StatusBar(ttk.Frame):
    """Status bar with message display"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        self.label = ttk.Label(self, textvariable=self.status_var, anchor=tk.W, padding=(5, 2))
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def set_status(self, message):
        """Set status message"""
        self.status_var.set(message)
        self.update_idletasks()
    
    def clear_status(self):
        """Clear status message"""
        self.status_var.set("Ready")
        self.update_idletasks()


class LogPanel(ttk.Frame):
    """Panel for displaying log messages"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Create log text area
        self.log_area = ScrolledText(self, height=6, width=70, font=('Arial', 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area.config(state=tk.DISABLED)
        
        # Create clear button
        self.clear_btn = ttk.Button(self, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def log_message(self, message, level="INFO"):
        """Add message to the log area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, formatted_message)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Clear the log area"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)


class SearchableCombobox(ttk.Frame):
    """Combobox with search functionality"""
    def __init__(self, parent, values=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.all_values = values or []
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._filter_values)
        self.search_entry = ttk.Entry(self, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.TOP, fill=tk.X)
        self.search_entry.bind("<Return>", self._select_first)
        
        # Dropdown combobox
        self.selected_var = tk.StringVar()
        self.combobox = ttk.Combobox(
            self,
            textvariable=self.selected_var,
            width=29,
            state="readonly"
        )
        self.combobox.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))
        
        # Set initial values
        self.set_values(self.all_values)
    
    def set_values(self, values):
        """Set available values for the combobox"""
        self.all_values = values
        self.combobox['values'] = values if values else ["No items available"]
    
    def get(self):
        """Get the selected value"""
        selected = self.selected_var.get()
        if selected in ["No items available", "No matching items"]:
            return None
        return selected
    
    def set(self, value):
        """Set the selected value"""
        if value in self.all_values:
            self.selected_var.set(value)
            # Clear search field
            self.search_var.set("")
    
    def clear(self):
        """Clear selection and search"""
        self.selected_var.set("")
        self.search_var.set("")
    
    def _filter_values(self, *args):
        """Filter values based on search text"""
        search_text = self.search_var.get().strip().lower()
        
        if not search_text:
            # If search is empty, show all values
            self.combobox['values'] = self.all_values if self.all_values else ["No items available"]
            return
        
        # Filter values that contain the search text
        filtered = [value for value in self.all_values if search_text in value.lower()]
        
        if filtered:
            self.combobox['values'] = filtered
        else:
            self.combobox['values'] = ["No matching items"]
    
    def _select_first(self, event=None):
        """Select the first item in the filtered list"""
        values = self.combobox['values']
        if values and values[0] not in ["No items available", "No matching items"]:
            self.combobox.current(0)
            # Trigger selection if needed
            self.combobox.event_generate("<<ComboboxSelected>>")


class FileListView(ttk.Frame):
    """File list with details view"""
    def __init__(self, parent, columns=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Define default columns if not provided
        if columns is None:
            columns = [
                {"id": "name", "text": "Name", "width": 200},
                {"id": "size", "text": "Size", "width": 100},
                {"id": "date", "text": "Date", "width": 150}
            ]
        
        # Create treeview
        self.tree = ttk.Treeview(self, columns=[col["id"] for col in columns], show="headings")
        
        # Configure columns and headings
        for col in columns:
            self.tree.heading(col["id"], text=col["text"])
            self.tree.column(col["id"], width=col.get("width", 100), anchor=col.get("anchor", "w"))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def populate(self, items):
        """Populate the list with items"""
        # Clear existing items
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # Add new items
        for item in items:
            self.tree.insert("", tk.END, values=item)
    
    def get_selected_item(self):
        """Get the selected item"""
        selected_items = self.tree.selection()
        if not selected_items:
            return None
        
        item_id = selected_items[0]
        values = self.tree.item(item_id, "values")
        return values
    
    def bind_double_click(self, callback):
        """Bind double-click event to a callback"""
        self.tree.bind("<Double-1>", callback)


def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.1f} GB"


def center_window(window, width, height):
    """Center a window on the screen"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")