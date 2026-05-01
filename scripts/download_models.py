import os
import paramiko
from dotenv import load_dotenv

def download_llms():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    models = {
        "Phi-2-Q4_K_M": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
        "Qwen2.5-1.5B-Instruct-Q4_K_M": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    }
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host}...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # 1. Create models directory
        model_dir = f"{project_path}/models/llm"
        print(f"Ensuring directory exists: {model_dir}")
        ssh.exec_command(f"mkdir -p {model_dir}")
        
        # 2. Download models
        for name, url in models.items():
            filename = url.split("/")[-1]
            dest = f"{model_dir}/{filename}"
            
            # Check if file already exists
            stdin, stdout, stderr = ssh.exec_command(f"ls {dest}")
            if stdout.read():
                print(f"Model {name} already exists at {dest}. Skipping.")
                continue
                
            print(f"Downloading {name} from Hugging Face...")
            print(f"URL: {url}")
            # Use wget with -c to continue if interrupted
            download_cmd = f"wget -c {url} -O {dest}"
            
            # We use exec_command but we need to wait or use a background process
            # Given these are large files, we'll run them one by one
            stdin, stdout, stderr = ssh.exec_command(download_cmd)
            
            # Monitoring progress might be hard via exec_command without blocking
            # but we can check the file size periodically
            print(f"Download started for {filename}. This may take a while...")
            # We wait for the command to finish
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                print(f"SUCCESS: {name} downloaded.")
            else:
                print(f"ERROR: Failed to download {name}. Exit code: {exit_status}")
                
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    download_llms()
