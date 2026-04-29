import os
import paramiko
from dotenv import load_dotenv

def create_shortcut():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    desktop_path = f"/home/{user}/Desktop"
    script_path = f"{desktop_path}/RUN_MIA_JETSON.sh"
    desktop_file_path = f"{desktop_path}/RUN_MIA_JETSON.desktop"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        print("Connected to Jetson!")
        
        # 1. Create a bash script just in case
        bash_content = f"""#!/bin/bash
cd {project_path}
python3 src/main.py
"""
        # 2. Create a .desktop file which is the Linux equivalent of a shortcut
        desktop_content = f"""[Desktop Entry]
Version=1.0
Name=RUN MIA JETSON
Comment=Start MIA AI System
Exec=gnome-terminal -- bash -c "cd {project_path} && python3 src/main.py; exec bash"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Application;
"""
        
        # Ensure Desktop directory exists
        ssh.exec_command(f"mkdir -p {desktop_path}")
        
        # Write bash script
        stdin, stdout, stderr = ssh.exec_command(f"cat > {script_path}")
        stdin.write(bash_content)
        stdin.channel.shutdown_write()
        
        # Write desktop shortcut
        stdin, stdout, stderr = ssh.exec_command(f"cat > {desktop_file_path}")
        stdin.write(desktop_content)
        stdin.channel.shutdown_write()
        
        # Make them executable
        ssh.exec_command(f"chmod +x {script_path}")
        ssh.exec_command(f"chmod +x {desktop_file_path}")
        # Ubuntu specific: allow launching the desktop file
        ssh.exec_command(f"gio trust {desktop_file_path}")
        
        print(f"Created executable shortcut on Jetson Desktop: {desktop_file_path}")
        
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    create_shortcut()
