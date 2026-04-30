"""
MIA_JETSON - Audio Diagnostics Script
Run this from your Windows PC to diagnose audio issues on the Jetson.
It will SSH into the Jetson and run a series of audio tests.
"""
import paramiko
import sys
import time

HOST = '10.0.0.9'
USER = 'mia'
PASSWORD = 'MIA_JETSON'

def run_ssh(ssh, cmd, timeout=15):
    """Execute a command via SSH and return output"""
    print(f"\n{'='*60}")
    print(f"COMMAND: {cmd}")
    print(f"{'='*60}")
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(f"STDOUT:\n{out}")
        if err:
            print(f"STDERR:\n{err}")
        if not out and not err:
            print("(no output)")
        return out, err
    except Exception as e:
        print(f"ERROR: {e}")
        return "", str(e)

def main():
    print("="*60)
    print("MIA JETSON - AUDIO DIAGNOSTICS")
    print("="*60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"\nConnecting to {HOST}...")
        ssh.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=10)
        print("Connected!\n")
    except Exception as e:
        print(f"FAILED to connect: {e}")
        sys.exit(1)
    
    # 1. List all sound cards
    print("\n" + "#"*60)
    print("# STEP 1: List ALSA Sound Cards")
    print("#"*60)
    run_ssh(ssh, "cat /proc/asound/cards")
    run_ssh(ssh, "aplay -l")
    
    # 2. Check ALSA default config
    print("\n" + "#"*60)
    print("# STEP 2: Check ALSA Default Configuration")
    print("#"*60)
    run_ssh(ssh, "cat /etc/asound.conf 2>/dev/null || echo 'No /etc/asound.conf'")
    run_ssh(ssh, "cat ~/.asoundrc 2>/dev/null || echo 'No ~/.asoundrc'")
    
    # 3. Check volume levels
    print("\n" + "#"*60)
    print("# STEP 3: Check Volume Levels")
    print("#"*60)
    run_ssh(ssh, "amixer -c 0 scontents 2>/dev/null || echo 'No mixer for card 0'")
    
    # 4. Set volume to max on card 0
    print("\n" + "#"*60)
    print("# STEP 4: Set Volume to MAX on Card 0")
    print("#"*60)
    run_ssh(ssh, "amixer -c 0 set Speaker 100% unmute 2>/dev/null; amixer -c 0 set PCM 100% unmute 2>/dev/null; amixer -c 0 set Master 100% unmute 2>/dev/null; echo 'Volume set attempts complete'")
    
    # 5. Test with speaker-test (2 seconds)
    print("\n" + "#"*60)
    print("# STEP 5: Test Audio with speaker-test (Card 0)")
    print("#"*60)
    run_ssh(ssh, "timeout 3 speaker-test -D plughw:0,0 -t sine -f 440 -l 1 2>&1 || echo 'speaker-test done'", timeout=10)
    
    # 6. Test with aplay directly
    print("\n" + "#"*60)
    print("# STEP 6: Test with aplay (generate and play a beep)")
    print("#"*60)
    # Generate a simple WAV beep using python and play it
    run_ssh(ssh, """python3 -c "
import struct, wave, math
srate = 44100
dur = 1.0
freq = 440
nframes = int(srate * dur)
with wave.open('/tmp/test_beep.wav', 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(srate)
    for i in range(nframes):
        val = int(32767 * math.sin(2 * math.pi * freq * i / srate))
        w.writeframes(struct.pack('<h', val))
print('Beep WAV created: /tmp/test_beep.wav')
" """)
    run_ssh(ssh, "aplay -D plughw:0,0 /tmp/test_beep.wav 2>&1", timeout=10)
    
    # 7. Test mpv with explicit ALSA device
    print("\n" + "#"*60)
    print("# STEP 7: Test mpv with explicit ALSA device")
    print("#"*60)
    run_ssh(ssh, "which mpv && mpv --version | head -1 || echo 'mpv not installed'")
    run_ssh(ssh, "mpv --no-video --no-terminal --audio-device=alsa/plughw:0,0 /tmp/test_beep.wav 2>&1 || echo 'mpv test done'", timeout=10)
    
    # 8. Check if ElevenLabs/Python env is working
    print("\n" + "#"*60)
    print("# STEP 8: Check Python Environment")
    print("#"*60)
    run_ssh(ssh, "cd /home/mia/MIA_JETSON && python3 -c 'from dotenv import load_dotenv; load_dotenv(\".env\"); import os; key=os.getenv(\"ELEVENLABS_API_KEY\"); print(f\"API Key present: {bool(key)}\"); print(f\"Key starts with: {key[:10]}...\" if key else \"NO KEY\")'")
    run_ssh(ssh, "python3 -c 'import elevenlabs; print(f\"ElevenLabs version: {getattr(elevenlabs, \"__version__\", \"unknown\")}\")'")
    
    # 9. Create/verify ALSA config for default device
    print("\n" + "#"*60)
    print("# STEP 9: Ensure ALSA Default Points to USB Audio")
    print("#"*60)
    # Create .asoundrc that forces card 0 as default
    asoundrc_content = """
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
"""
    run_ssh(ssh, f'echo \'{asoundrc_content.strip()}\' > ~/.asoundrc && echo "~/.asoundrc updated" && cat ~/.asoundrc')
    
    # 10. Final test after config update
    print("\n" + "#"*60)
    print("# STEP 10: Final Test After Config Update")
    print("#"*60)
    run_ssh(ssh, "aplay /tmp/test_beep.wav 2>&1", timeout=10)
    
    print("\n" + "="*60)
    print("DIAGNOSTICS COMPLETE")
    print("="*60)
    print("""
NEXT STEPS:
1. If Steps 5/6 produced sound → Hardware is fine, issue is in Python playback
2. If Step 7 produced sound → mpv works, issue was ALSA default config (now fixed in Step 9)
3. If no steps produced sound → Check physical speaker connection / power
4. After diagnostics, try running MIA again:
   cd /home/mia/MIA_JETSON && python3 -m src.main
""")
    
    ssh.close()

if __name__ == "__main__":
    main()
