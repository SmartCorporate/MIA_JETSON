import paramiko
import sys

host = '10.0.0.9'
user = 'mia'
password = 'MIA_JETSON'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=host, username=user, password=password, timeout=10)
    
    commands = {
        "USB Devices (lsusb)": "lsusb",
        "Playback Audio (aplay -l)": "aplay -l",
        "Capture Audio (arecord -l)": "arecord -l",
        "Video Devices (ls /dev/video*)": "ls -l /dev/video*"
    }
    
    for title, cmd in commands.items():
        print(f"\n=== {title} ===")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode().strip())
        err = stderr.read().decode().strip()
        if err:
            print(f"Error: {err}")
            
    ssh.close()
except Exception as e:
    print(f"Failed to connect: {e}")
