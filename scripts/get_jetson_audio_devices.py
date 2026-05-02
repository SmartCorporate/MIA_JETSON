import paramiko
import os
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    host = '10.0.0.9'
    user = 'mia'
    password = 'MIA_JETSON'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)

    print("Querying audio devices...")
    stdin, stdout, stderr = ssh.exec_command("python3 -c 'import sounddevice as sd; print(sd.query_devices())'")
    devices = stdout.read().decode()
    print(devices)
    
    ssh.close()

if __name__ == "__main__":
    main()
