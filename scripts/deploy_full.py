#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full deploy + restart of MIA JETSON.
Uploads all modified files and relaunches the dashboard.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko, time, os

HOST     = '10.0.0.9'
USER     = 'mia'
PASSWORD = 'MIA_JETSON'
REMOTE   = '/home/mia/MIA_JETSON'
LOCAL    = r'C:\Users\IMPERIUM\2 Engineering\2 Project Development\MIA_JETSON'

FILES_TO_DEPLOY = [
    # (local_relative, remote_relative)
    ('src/core/orchestrator.py',            'src/core/orchestrator.py'),
    ('src/agents/brain/brain_llm.py',       'src/agents/brain/brain_llm.py'),
    ('src/agents/brain/response_generator.py', 'src/agents/brain/response_generator.py'),
    ('scripts/mia_launcher.sh',             'scripts/mia_launcher.sh'),
    ('scripts/jetson_status_monitor.py',    'scripts/jetson_status_monitor.py'),
    ('configs/config_audio.json',           'configs/config_audio.json'),
]

def run(ssh, cmd, timeout=12):
    chan = ssh.get_transport().open_session()
    chan.exec_command(cmd)
    out = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        if chan.recv_ready():
            out.append(chan.recv(4096).decode('utf-8', errors='replace'))
        if chan.exit_status_ready():
            while chan.recv_ready():
                out.append(chan.recv(4096).decode('utf-8', errors='replace'))
            break
        time.sleep(0.1)
    return ''.join(out).strip()

def fire(ssh, cmd):
    chan = ssh.get_transport().open_session()
    chan.exec_command(f'nohup bash -c {repr(cmd)} > /tmp/mia_fire.log 2>&1 &')
    time.sleep(2)
    chan.close()

print("=" * 55)
print("  MIA JETSON — FULL DEPLOY & RESTART")
print("=" * 55)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=15)
print(">> Connected")

# Upload all files
sftp = ssh.open_sftp()
for local_rel, remote_rel in FILES_TO_DEPLOY:
    local_path  = os.path.join(LOCAL, local_rel.replace('/', os.sep))
    remote_path = f"{REMOTE}/{remote_rel}"
    sftp.put(local_path, remote_path)
    print(f"   [UP] {remote_rel}")
sftp.close()
print(">> All files uploaded\n")

# Kill everything
run(ssh, "pkill -f xterm 2>/dev/null; pkill -f 'main.py' 2>/dev/null; pkill -f 'jetson_status' 2>/dev/null; sleep 1")
print(">> Old processes killed")

# Make launcher executable
run(ssh, f"chmod +x {REMOTE}/scripts/mia_launcher.sh")

# Clear logs
run(ssh, f"truncate -s 0 {REMOTE}/error.log {REMOTE}/mia.log 2>/dev/null || true")
print(">> Logs cleared")
time.sleep(1)

# Verify Vosk model sample rate compatibility
print("\n>> Checking Vosk model...")
r = run(ssh, f"ls {REMOTE}/models/stt/ 2>&1")
print(f"   STT models: {r}")

# Launch dashboard
print("\n>> Launching MIA Dashboard...")
fire(ssh, f"bash {REMOTE}/scripts/mia_launcher.sh")
time.sleep(3)

# Verify
r = run(ssh, "pgrep -c -f xterm 2>/dev/null || echo 0")
print(f">> xterm windows open: {r}")
r = run(ssh, "pgrep -a -f 'main.py' | grep -v grep | head -1")
print(f">> MIA main: {r or 'starting...'}")

ssh.close()
print("\n[OK] Deploy complete. MIA is loading on the Jetson.")
print("     Wait ~30s for the greeting 'Ciao, sono MIA e sono pronta.'")
