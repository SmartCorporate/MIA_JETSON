import os
import paramiko
from dotenv import load_dotenv

def build_isolation_fix():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # 1. Install all build dependencies in the main env
        print("Installing build dependencies to avoid isolation issues...")
        build_deps = "scikit-build-core pyproject-metadata pathspec packaging"
        cmd = f"echo '{password}' | sudo -S python3 -m pip install {build_deps}"
        ssh.exec_command(cmd)
        
        # 2. Install llama-cpp-python with --no-build-isolation
        print("Installing llama-cpp-python with --no-build-isolation...")
        install_cmd = (
            f"export PATH=/usr/local/cuda/bin:$PATH && "
            f"export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH && "
            f"CMAKE_ARGS='-DLLAMA_CUBLAS=on' echo '{password}' | sudo -S python3 -m pip install llama-cpp-python --no-cache-dir --no-build-isolation > {project_path}/install_llama.log 2>&1 &"
        )
        ssh.exec_command(install_cmd)
        
        print("\nInstallation restarted with build isolation fix.")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    build_isolation_fix()
