import os
import paramiko
from dotenv import load_dotenv

def final_install():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host} for final installation...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # 1. Upgrade build tools using python3 -m pip (more reliable)
        print("Upgrading build tools (pip, setuptools, wheel, packaging, scikit-build-core)...")
        upgrade_cmd = (
            "python3 -m pip install --upgrade pip setuptools wheel && "
            "python3 -m pip install --upgrade \"packaging>=24.0\" scikit-build-core"
        )
        stdin, stdout, stderr = ssh.exec_command(upgrade_cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 2. Install llama-cpp-python with CUDA support
        print("Installing llama-cpp-python with CUDA support...")
        install_cmd = (
            f"export PATH=/usr/local/cuda/bin:$PATH && "
            f"export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH && "
            f"CMAKE_ARGS='-DLLAMA_CUBLAS=on' nohup python3 -m pip install llama-cpp-python --no-cache-dir > {project_path}/install_llama.log 2>&1 &"
        )
        ssh.exec_command(install_cmd)
        
        print("\nInstallation process restarted in background.")
        print(f"Monitor progress with: tail -f {project_path}/install_llama.log")
        
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    final_install()
