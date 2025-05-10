import os
import paramiko
import stat

class SSHClient:
    def __init__(self, host, port, username, password, remote_dir):
        """Initialize SSH client with connection details"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_dir = remote_dir
        self.client = None
        self.sftp = None
    
    def connect(self):
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self.host, 
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            print(self.client)
            # Check if the remote directory exists
            return True, None
        except Exception as e:
            error_msg = f"SSH Connection Error: {str(e)}"
            return False, error_msg
    
    def open_sftp(self):
        """Open SFTP connection"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return False, error
        
        try:
            self.sftp = self.client.open_sftp()
            return True, None
        except Exception as e:
            error_msg = f"SFTP Connection Error: {str(e)}"
            return False, error_msg
    
    def close(self):
        """Close SSH and SFTP connections"""
        if self.sftp:
            try:
                self.sftp.close()
            except:
                pass
            finally:
                self.sftp = None
        
        if self.client:
            try:
                self.client.close()
            except:
                pass
            finally:
                self.client = None
    
    def execute_command(self, command):
        """Execute a command on the remote server"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return None, error, -1
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            return output, error, exit_status
        except Exception as e:
            return None, str(e), -1
    
    def create_folder(self, folder_name):
        """Create a folder on the remote server"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return False, error
        
        remote_folder_path = os.path.join(self.remote_dir, folder_name).replace("\\", "/")
        
        try:
            # Windows command to create directory
            output, error, exit_status = self.execute_command(f'mkdir "{remote_folder_path}"')
            
            # Check if the folder creation was successful or if the folder already exists
            if exit_status == 0 or "already exists" in error.lower():
                return True, remote_folder_path
            else:
                return False, error
        except Exception as e:
            return False, str(e)
    
    def list_folders(self):
        """List all folders in the remote directory"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return [], error
        
        try:
            # Windows command to list directories
            output, error, exit_status = self.execute_command(f'dir "{self.remote_dir}" /b /ad')
            
            if exit_status == 0:
                folders = [folder for folder in output.split('\r\n') if folder]
                return folders, None
            else:
                return [], error
        except Exception as e:
            return [], str(e)
    
    def list_files(self, folder_name):
        """List all files in a remote folder"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return [], error
        
        remote_folder_path = os.path.join(self.remote_dir, folder_name).replace("\\", "/")
        
        try:
            # Windows command to list files (exclude directories)
            output, error, exit_status = self.execute_command(f'dir "{remote_folder_path}" /b /a-d')
            
            if exit_status == 0:
                files = [file for file in output.split('\r\n') if file]
                return files, None
            else:
                return [], error
        except Exception as e:
            return [], str(e)
    
    def get_file_info(self, folder_name, file_name):
        """Get file information (size, modification time)"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return None, error
        
        remote_path = os.path.join(self.remote_dir, folder_name, file_name).replace("\\", "/")
        
        try:
            # Open SFTP if not already open
            if not self.sftp:
                success, error = self.open_sftp()
                if not success:
                    return None, error
            
            # Get file stats
            file_stat = self.sftp.stat(remote_path)
            file_size = file_stat.st_size
            file_mtime = file_stat.st_mtime
            
            return {"size": file_size, "mtime": file_mtime}, None
        except Exception as e:
            return None, str(e)
    
    def upload_file(self, local_file_path, folder_name):
        """Upload a file to a remote folder"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return None, error
        
        try:
            # Ensure the folder exists
            success, result = self.create_folder(folder_name)
            if not success:
                return None, result
            
            # Open SFTP if not already open
            if not self.sftp:
                success, error = self.open_sftp()
                if not success:      
                    return None, error
            
            # Construct remote file path
            file_name = os.path.basename(local_file_path)
            remote_folder_path = os.path.join(self.remote_dir, folder_name).replace("\\", "/")
            remote_file_path = os.path.join(remote_folder_path, file_name).replace("\\", "/")
            
            # Upload file
            self.sftp.put(local_file_path, remote_file_path)
            
            # Get file stats for verification
            file_stat = self.sftp.stat(remote_file_path)
            file_size = file_stat.st_size
            
            return {"path": remote_file_path, "size": file_size}, None
        except Exception as e:
            return None, str(e)
    
    def download_file(self, folder_name, file_name, local_directory):
        """Download a file from a remote folder"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return None, error
        
        try:
            # Open SFTP if not already open
            if not self.sftp:
                success, error = self.open_sftp()
                if not success:
                    return None, error
            
            # Construct paths
            remote_path = os.path.join(self.remote_dir, folder_name, file_name).replace("\\", "/")
            local_path = os.path.join(local_directory, file_name)
            
            # Download file
            self.sftp.get(remote_path, local_path)
            
            return {"path": local_path}, None
        except Exception as e:
            return None, str(e)
    
    def delete_file(self, folder_name, file_name):
        """Delete a file from a remote folder"""
        if not self.client:
            success, error = self.connect()
            if not success:
                return False, error
        
        try:
            # Open SFTP if not already open
            if not self.sftp:
                success, error = self.open_sftp()
                if not success:
                    return False, error
            
            # Construct remote file path
            remote_path = os.path.join(self.remote_dir, folder_name, file_name).replace("\\", "/")
            
            # Remove file
            self.sftp.remove(remote_path)
            
            return True, None
        except Exception as e:
            return False, str(e)