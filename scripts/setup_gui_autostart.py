import os
import paramiko
from dotenv import load_dotenv

def setup_gui_autostart():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host} to setup GUI autostart...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # 1. Disable the background systemd service to avoid conflicts
        print("Disabling background systemd service...")
        ssh.exec_command(f"echo '{password}' | sudo -S systemctl stop mia_jetson.service")
        ssh.exec_command(f"echo '{password}' | sudo -S systemctl disable mia_jetson.service")
        
        # 2. Create autostart directory if it doesn't exist
        autostart_dir = f"/home/{user}/.config/autostart"
        ssh.exec_command(f"mkdir -p {autostart_dir}")
        
        # 3. Create the .desktop file for autostart
        desktop_content = f"""[Desktop Entry]
Type=Application
Exec=gnome-terminal -- bash -c "cd {project_path} && python3 -u src/main.py; exec bash"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=MIA JETSON
Comment=Start MIA in a terminal window at login
Icon=utilities-terminal
"""
        
        autostart_file = f"{autostart_dir}/mia_autostart.desktop"
        print(f"Creating autostart entry at {autostart_file}...")
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > {autostart_file}")
        stdin.write(desktop_content)
        stdin.channel.shutdown_write()
        
        # 4. Make it executable
        ssh.exec_command(f"chmod +x {autostart_file}")
        
        print("\nSUCCESS: MIA will now open in a terminal window automatically when the Jetson logs in.")
        print("IMPORTANT: Ensure the Jetson is set to 'Auto-login' in Ubuntu settings for this to work on power-on.")
        
    except Exception as e:
        print(f"Setup failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    setup_gui_autostart()
