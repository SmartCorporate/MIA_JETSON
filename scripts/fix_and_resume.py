import os
import paramiko
from dotenv import load_dotenv

def fix_and_resume():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host}...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # 1. Kill stalled wget
        print("Cleaning up stalled wget...")
        ssh.exec_command("pkill wget")
        
        # 2. Resume downloads with robust parameters
        models = {
            "Phi-2": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
            "Qwen2.5-1.5B": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
        }
        
        for name, url in models.items():
            filename = url.split("/")[-1]
            dest = f"{project_path}/models/llm/{filename}"
            print(f"Resuming download for {name}...")
            # --continue to resume, --tries=0 for infinite, --timeout for connection
            cmd = f"nohup wget -c --tries=0 --read-timeout=20 --timeout=15 {url} -O {dest} > {project_path}/download_{name}.log 2>&1 &"
            ssh.exec_command(cmd)
            
        # 3. Install prerequisites for llama-cpp
        print("Installing prerequisites for llama-cpp-python...")
        pre_req_cmd = f"echo '{password}' | sudo -S apt-get update && echo '{password}' | sudo -S apt-get install -y python3-pip cmake build-essential"
        ssh.exec_command(pre_req_cmd)
        
        # 4. Start llama-cpp-python installation in background
        print("Starting llama-cpp-python installation with prerequisite upgrades...")
        install_cmd = (
            f"export PATH=/usr/local/cuda/bin:$PATH && "
            f"export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH && "
            f"pip3 install --upgrade pip setuptools wheel packaging scikit-build-core && "
            f"CMAKE_ARGS='-DLLAMA_CUBLAS=on' nohup pip3 install llama-cpp-python > {project_path}/install_llama.log 2>&1 &"
        )
        ssh.exec_command(install_cmd)
        
        print("\nAll tasks (Downloads & Installation) are now running in the background.")
        print(f"Check logs on Jetson: download_*.log and install_llama.log")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    fix_and_resume()
