import os
import paramiko
from dotenv import load_dotenv

def sudo_install():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # 1. Upgrade everything with sudo
        print("Upgrading build tools with sudo...")
        cmd = f"echo '{password}' | sudo -S python3 -m pip install --upgrade pip setuptools wheel packaging scikit-build-core"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        # 2. Install llama-cpp-python with sudo
        print("Installing llama-cpp-python with sudo and CUDA support...")
        install_cmd = (
            f"export PATH=/usr/local/cuda/bin:$PATH && "
            f"export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH && "
            f"CMAKE_ARGS='-DLLAMA_CUBLAS=on' echo '{password}' | sudo -S python3 -m pip install llama-cpp-python --no-cache-dir > {project_path}/install_llama.log 2>&1 &"
        )
        ssh.exec_command(install_cmd)
        
        print("\nInstallation restarted with sudo.")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    sudo_install()
