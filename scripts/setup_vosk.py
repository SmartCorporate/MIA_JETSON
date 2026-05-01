import os
import paramiko
from dotenv import load_dotenv

def setup_vosk():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # 1. Create models/stt directory
        stt_dir = f"{project_path}/models/stt"
        ssh.exec_command(f"mkdir -p {stt_dir}")
        
        # 2. Download and unzip Vosk Small English model
        print("Downloading Vosk model...")
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        zip_file = f"{stt_dir}/vosk-en.zip"
        
        # Check if already exists
        stdin, stdout, stderr = ssh.exec_command(f"ls {stt_dir}/vosk-model-small-en-us-0.15")
        if stdout.read():
            print("Vosk model already exists. Skipping download.")
        else:
            cmd = f"wget -c {url} -O {zip_file} && unzip {zip_file} -d {stt_dir} && rm {zip_file}"
            print("Starting download and extraction (this may take a minute)...")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.channel.recv_exit_status()
            print("Vosk model installed.")

        # 3. Download and unzip Vosk Small Italian model (for bilingual support)
        print("Downloading Italian Vosk model...")
        url_it = "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip"
        zip_file_it = f"{stt_dir}/vosk-it.zip"
        
        stdin, stdout, stderr = ssh.exec_command(f"ls {stt_dir}/vosk-model-small-it-0.22")
        if stdout.read():
            print("Italian Vosk model already exists. Skipping download.")
        else:
            cmd_it = f"wget -c {url_it} -O {zip_file_it} && unzip {zip_file_it} -d {stt_dir} && rm {zip_file_it}"
            print("Starting Italian download...")
            stdin, stdout, stderr = ssh.exec_command(cmd_it)
            stdout.channel.recv_exit_status()
            print("Italian Vosk model installed.")
            
        print("\nSUCCESS: Vosk models are ready.")
        
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    setup_vosk()
