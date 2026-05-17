#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read error log and key system info from Jetson."""
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
        if chan.recv_ready(): out.append(chan.recv(8192).decode('utf-8','replace'))
        if chan.exit_status_ready(): break
        time.sleep(0.1)
    return ''.join(out).strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=10)

print("=== ERROR LOG (last 50 lines) ===")
print(run(ssh, f"tail -50 {REMOTE}/error.log 2>/dev/null || echo 'No error.log'"))

print("\n=== MIA LOG (last 30 lines) ===")
print(run(ssh, f"tail -30 {REMOTE}/mia.log 2>/dev/null || echo 'No mia.log'"))

print("\n=== JOURNAL / DMESG Over-current ===")
print(run(ssh, "dmesg | grep -i 'over.current\\|throttle\\|overcurrent' | tail -20"))

print("\n=== POWER / tegrastats ===")
print(run(ssh, "timeout 2 tegrastats 2>/dev/null | head -1"))

print("\n=== PROCESSES ===")
print(run(ssh, "pgrep -a -f 'main.py\\|stt\\|voice\\|whisper\\|vosk' | head -10"))

print("\n=== AUDIO DEVICES ===")
print(run(ssh, "arecord -l 2>&1 | head -20"))

ssh.close()
