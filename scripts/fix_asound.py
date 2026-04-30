"""Fix /etc/asound.conf on Jetson to point to USB speakers instead of Tegra APE"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.0.0.9', username='mia', password='MIA_JETSON', timeout=10)
print("Connected!")

# Backup original
stdin, stdout, stderr = ssh.exec_command("sudo cp /etc/asound.conf /etc/asound.conf.nvidia_bak", get_pty=True)
time.sleep(1)
stdin.write("MIA_JETSON\n")
stdin.flush()
time.sleep(2)
print("Backup:", stdout.read().decode(), stderr.read().decode())

# Write new asound.conf via heredoc
new_conf_cmd = """sudo tee /etc/asound.conf << 'ASOUNDEOF'
# MIA JETSON - Audio Config
# Force USB speakers (Card 0) as default output

pcm.!default {
    type plug
    slave {
        pcm "hw:0,0"
    }
}

ctl.!default {
    type hw
    card 0
}
ASOUNDEOF"""

stdin, stdout, stderr = ssh.exec_command(new_conf_cmd, get_pty=True)
time.sleep(1)
stdin.write("MIA_JETSON\n")
stdin.flush()
time.sleep(2)
print("Write result:", stdout.read().decode())

# Verify
stdin, stdout, stderr = ssh.exec_command("cat /etc/asound.conf")
print("\nNew /etc/asound.conf:")
print(stdout.read().decode())

# Also test that default audio now works without specifying device
stdin, stdout, stderr = ssh.exec_command("aplay /tmp/test_beep.wav 2>&1")
print("\naplay test (no device specified):", stdout.read().decode())

# Now push the updated voice_agent.py to Jetson
print("\nDeploying updated voice_agent.py...")
sftp = ssh.open_sftp()
local_path = r"src\audio\voice_agent.py"
remote_path = "/home/mia/MIA_JETSON/src/audio/voice_agent.py"
try:
    sftp.put(local_path, remote_path)
    print(f"Deployed {remote_path} successfully!")
except Exception as e:
    print(f"Deploy error: {e}")
sftp.close()

# Test MIA speak
print("\n--- Testing MIA speak ---")
stdin, stdout, stderr = ssh.exec_command(
    "cd /home/mia/MIA_JETSON && python3 -c \""
    "import os; os.environ['ELEVENLABS_API_KEY']='sk_771a8c9419cde806946a5d92810524c52e399d147e172a58'; "
    "from src.audio.voice_agent import VoiceAgent; "
    "v = VoiceAgent(); "
    "v.speak('Hello, I am Mia. Audio test successful.')"
    "\"",
    timeout=60
)
time.sleep(15)
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())

ssh.close()
print("\nDone!")
