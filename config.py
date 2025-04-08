import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server configuration
SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
REMOTE_DIR = os.getenv("REMOTE_PATH")

# Application configuration
APP_NAME = "SSH File Manager"
APP_VERSION = "1.0.0"
DB_NAME = "ssh_manager.db"

# UI configuration
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
THEME = "clam"  # Options: 'clam', 'alt', 'default', 'classic'

# Validate required configuration
def validate_config():
    """Validate that all required configuration variables are set"""
    required_vars = {
        "SSH_HOST": SSH_HOST,
        "SSH_USER": SSH_USER,
        "SSH_PASSWORD": SSH_PASSWORD,
        "REMOTE_DIR": REMOTE_DIR
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        return False, f"Missing required configuration: {', '.join(missing)}"
    
    return True, None