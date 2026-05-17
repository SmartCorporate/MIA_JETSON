#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launch full MIA dashboard on Jetson via SSH."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko, time

HOST='10.0.0.9'; USER='mia'; PASSWORD='MIA_JETSON'
REMOTE='/home/mia/MIA_JETSON'

def run(ssh, cmd, timeout=10):
    chan = ssh.get_transport().open_session()
    chan.exec_command(cmd)
    out=[]
    deadline = time.time() + timeout
    while time.time() < deadline:
        if chan.recv_ready(): out.append(chan.recv(4096).decode('utf-8','replace'))
        if chan.exit_status_ready(): break
        time.sleep(0.1)
    return ''.join(out).strip()

def fire(ssh, cmd):
    """Fire and forget a background command."""
    chan = ssh.get_transport().open_session()
    chan.exec_command(f'nohup bash -c {repr(cmd)} > /tmp/mia_launch.log 2>&1 &')
    time.sleep(1.5)
    chan.close()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=10)
print(">> Connected to Jetson")

# Kill any stale processes
run(ssh, "pkill -f 'main.py' 2>/dev/null; pkill -f xterm 2>/dev/null; sleep 1")
print(">> Cleaned up old processes")
time.sleep(1)

# Launch full dashboard (all 4 terminals)
print(">> Launching MIA dashboard (4 terminals)...")
fire(ssh, f"bash {REMOTE}/scripts/mia_launcher.sh")
print(">> Dashboard launched!")
time.sleep(3)

# Verify
r = run(ssh, "pgrep -a -f 'main.py' | head -2")
print(f">> main.py: {r or 'starting...'}")
r = run(ssh, "pgrep -a -f 'jetson_status_monitor' | head -2")
print(f">> monitor: {r or 'not yet'}")

ssh.close()
print("\n[OK] MIA launched. Check the Jetson screen.")
