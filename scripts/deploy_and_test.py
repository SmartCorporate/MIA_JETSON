"""Deploy and test speech speed fix v2 (ffmpeg atempo)"""
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.0.0.9', username='mia', password='MIA_JETSON', timeout=10)
print('Connected!')

sftp = ssh.open_sftp()
sftp.put(r'src\audio\voice_agent.py', '/home/mia/MIA_JETSON/src/audio/voice_agent.py')
sftp.put(r'configs\config_voice.json', '/home/mia/MIA_JETSON/configs/config_voice.json')
sftp.close()
print('Files deployed!')

# Write test script on Jetson
test_script = """
import os, sys
os.environ['ELEVENLABS_API_KEY'] = 'sk_771a8c9419cde806946a5d92810524c52e399d147e172a58'
sys.path.insert(0, '/home/mia/MIA_JETSON')
from src.audio.voice_agent import VoiceAgent
v = VoiceAgent()
v.speak("Hello. I am Mia. My audio systems are online and ready.")
"""

stdin, stdout, stderr = ssh.exec_command("cat > /tmp/test_mia_voice.py << 'PYEOF'\n" + test_script + "\nPYEOF")
stdout.read()

print('\nTesting MIA voice at speed 0.85x (via ffmpeg atempo)...')
stdin, stdout, stderr = ssh.exec_command("python3 /tmp/test_mia_voice.py", timeout=60)
time.sleep(30)
print('OUT:', stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)
ssh.close()
print('Done!')
