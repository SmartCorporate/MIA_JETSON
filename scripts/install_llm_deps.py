import os
import paramiko
from dotenv import load_dotenv

def install_dependencies():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host} to install LLM dependencies...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # Install llama-cpp-python
        # On Jetson, we want CUDA support
        print("Installing llama-cpp-python with CUDA support (this may take 5-10 minutes)...")
        # We use a long timeout for this command
        # Note: We need to set CUDA paths if they are not in the environment
        cmd = (
            "export PATH=/usr/local/cuda/bin:$PATH && "
            "export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH && "
            "CMAKE_ARGS='-DLLAMA_CUBLAS=on' pip3 install llama-cpp-python"
        )
        
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=900)
        
        # We don't block here because it takes too long
        # Instead, we'll check later
        print("Installation command sent. Check mia.log or run check script later.")
        
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    install_dependencies()
