import os
import platform
import subprocess

def open_file_explorer(path):
    """Open file explorer at specified path"""
    if os.path.exists(path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", path])
        else:  # Linux
            subprocess.call(["xdg-open", path])
        return True
    return False

def ensure_dir_exists(directory):
    """Ensure directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return os.path.exists(directory)

def get_file_extension(file_path):
    """Get file extension from path"""
    return os.path.splitext(file_path)[1].lower()

def is_valid_file_type(file_path, allowed_extensions=None):
    """Check if file is of an allowed type"""
    if allowed_extensions is None:
        return True
    
    ext = get_file_extension(file_path)
    return ext in allowed_extensions