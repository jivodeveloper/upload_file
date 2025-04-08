import os
import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name, app_directory=None):
        """Initialize the database manager"""
        if app_directory is None:
            app_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.db_path = os.path.join(app_directory, db_name)
        self.conn = None
        self.cursor = None
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with necessary tables"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create folders table if it doesn't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    full_path TEXT,
                    created_at TIMESTAMP
                )
            ''')
            
            # Create files table if it doesn't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    folder_id INTEGER,
                    local_path TEXT,
                    remote_path TEXT,
                    size INTEGER,
                    uploaded_at TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders (id),
                    UNIQUE (folder_id, name)
                )
            ''')
            
            self.conn.commit()
            return True, None
        except Exception as e:
            error_msg = f"Database initialization error: {str(e)}"
            return False, error_msg
    
    def add_folder(self, folder_name, full_path):
        """Add a folder to the database"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute(
                "INSERT OR IGNORE INTO folders (name, full_path, created_at) VALUES (?, ?, ?)",
                (folder_name, full_path, current_time)
            )
            self.conn.commit()
            return True, None
        except Exception as e:
            error_msg = f"Database error when adding folder: {str(e)}"
            return False, error_msg
    
    def get_all_folders(self):
        """Get all folders from the database"""
        try:
            self.cursor.execute("SELECT id, name, full_path FROM folders ORDER BY name")
            return self.cursor.fetchall(), None
        except Exception as e:
            error_msg = f"Error getting folders: {str(e)}"
            return [], error_msg
    
    def get_folder_names(self):
        """Get all folder names from the database"""
        try:
            self.cursor.execute("SELECT name FROM folders ORDER BY name")
            return [row[0] for row in self.cursor.fetchall()], None
        except Exception as e:
            error_msg = f"Error getting folder names: {str(e)}"
            return [], error_msg
    
    def get_folder_id(self, folder_name):
        """Get folder ID by name"""
        try:
            self.cursor.execute("SELECT id FROM folders WHERE name = ?", (folder_name,))
            result = self.cursor.fetchone()
            return result[0] if result else None, None
        except Exception as e:
            error_msg = f"Error getting folder ID: {str(e)}"
            return None, error_msg
    
    def get_folder_path(self, folder_name):
        """Get folder path by name"""
        try:
            self.cursor.execute("SELECT full_path FROM folders WHERE name = ?", (folder_name,))
            result = self.cursor.fetchone()
            return result[0] if result else None, None
        except Exception as e:
            error_msg = f"Error getting folder path: {str(e)}"
            return None, error_msg
    
    def clear_folders(self):
        """Clear all folders from the database"""
        try:
            self.cursor.execute("DELETE FROM folders")
            self.conn.commit()
            return True, None
        except Exception as e:
            error_msg = f"Error clearing folders: {str(e)}"
            return False, error_msg
    
    def add_file(self, file_name, folder_name, local_path, remote_path, file_size):
        """Add a file to the database"""
        try:
            # Get folder ID
            folder_id, error = self.get_folder_id(folder_name)
            if error or not folder_id:
                return False, "Folder not found in database"
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute(
                "INSERT OR REPLACE INTO files (name, folder_id, local_path, remote_path, size, uploaded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (file_name, folder_id, local_path, remote_path, file_size, current_time)
            )
            self.conn.commit()
            return True, None
        except Exception as e:
            error_msg = f"Database error when adding file: {str(e)}"
            return False, error_msg
    
    def get_files_in_folder(self, folder_name):
        """Get all files in a folder"""
        try:
            folder_id, error = self.get_folder_id(folder_name)
            if error or not folder_id:
                return [], "Folder not found in database"
            
            self.cursor.execute(
                "SELECT id, name, local_path, remote_path, size, uploaded_at "
                "FROM files WHERE folder_id = ? ORDER BY name",
                (folder_id,)
            )
            return self.cursor.fetchall(), None
        except Exception as e:
            error_msg = f"Error getting files in folder: {str(e)}"
            return [], error_msg
    
    def get_file_by_name(self, folder_name, file_name):
        """Get file information by folder name and file name"""
        try:
            folder_id, error = self.get_folder_id(folder_name)
            if error or not folder_id:
                return None, "Folder not found in database"
            
            self.cursor.execute(
                "SELECT id, local_path, remote_path, size FROM files "
                "WHERE folder_id = ? AND name = ?",
                (folder_id, file_name)
            )
            return self.cursor.fetchone(), None
        except Exception as e:
            error_msg = f"Error getting file info: {str(e)}"
            return None, error_msg
    
    def delete_file(self, file_id):
        """Delete a file from the database by ID"""
        try:
            self.cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
            self.conn.commit()
            return True, None
        except Exception as e:
            error_msg = f"Error deleting file: {str(e)}"
            return False, error_msg
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()