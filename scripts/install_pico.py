import os
import paramiko
from dotenv import load_dotenv

def install_pico():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host} to install pico2wave...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # Command to install libttspico-utils
        print("Running sudo apt-get update and install libttspico-utils...")
        # We use -S to pass the password to sudo
        install_cmd = f"echo '{password}' | sudo -S apt-get update && echo '{password}' | sudo -S apt-get install -y libttspico-utils"
        
        stdin, stdout, stderr = ssh.exec_command(install_cmd)
        
        # Read output
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print("STDOUT:", output)
        print("STDERR:", error)
        
        # Verify installation
        stdin, stdout, stderr = ssh.exec_command("which pico2wave")
        res = stdout.read().decode().strip()
        if res:
            print(f"\nSUCCESS: pico2wave installed at {res}")
        else:
            print("\nFAILURE: pico2wave not found after installation.")
            
    except Exception as e:
        print(f"Installation failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    install_pico()
