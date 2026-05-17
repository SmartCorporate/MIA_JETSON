#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy jetson_status_monitor.py to Jetson and restart the blue terminal.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko, time, os

HOST     = '10.0.0.9'
USER     = 'mia'
PASSWORD = 'MIA_JETSON'
REMOTE   = '/home/mia/MIA_JETSON'
LOCAL    = r'C:\Users\IMPERIUM\2 Engineering\2 Project Development\MIA_JETSON'

def run(ssh, cmd, timeout=15):
    chan = ssh.get_transport().open_session()
    chan.exec_command(cmd)
    out_buf, err_buf = [], []
    deadline = time.time() + timeout
    while time.time() < deadline:
        if chan.recv_ready():
            out_buf.append(chan.recv(4096).decode('utf-8', errors='replace'))
        if chan.recv_stderr_ready():
            err_buf.append(chan.recv_stderr(4096).decode('utf-8', errors='replace'))
        if chan.exit_status_ready():
            while chan.recv_ready():
                out_buf.append(chan.recv(4096).decode('utf-8', errors='replace'))
            break
        time.sleep(0.1)
    return ''.join(out_buf).strip(), ''.join(err_buf).strip()

def fire_and_forget(ssh, cmd):
    """Launch a background command without waiting for it."""
    chan = ssh.get_transport().open_session()
    chan.exec_command(f'nohup bash -c {repr(cmd)} > /tmp/mia_xterm_launch.log 2>&1 &')
    time.sleep(1)
    chan.close()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=10)
print(">> Connected to Jetson")

# Upload new monitor
sftp = ssh.open_sftp()
sftp.put(
    os.path.join(LOCAL, 'scripts', 'jetson_status_monitor.py'),
    f'{REMOTE}/scripts/jetson_status_monitor.py'
)
print(">> Uploaded jetson_status_monitor.py")

# Also upload mia_launcher.sh in case it needs a restart
sftp.put(
    os.path.join(LOCAL, 'scripts', 'mia_launcher.sh'),
    f'{REMOTE}/scripts/mia_launcher.sh'
)
print(">> Uploaded mia_launcher.sh")
sftp.close()

# Kill old status monitor windows only (keep MIA main running)
out, err = run(ssh, "pkill -f 'jetson_status_monitor' 2>/dev/null; echo done")
print(f">> Killed old status monitor: {out}")
time.sleep(1)

# Restart only the status monitor window (AZZURRO)
restart_cmd = (
    "export DISPLAY=:0; "
    "export XAUTHORITY=/run/user/1000/gdm/Xauthority; "
    "xhost +local:mia > /dev/null 2>&1; "
    "xterm -title 'MIA - SYSTEM STATUS (AZZURRO)' "
    "-geometry 100x32+10+500 "
    "-fa 'Monospace' -fs 10 "
    "-bg black -fg '#00FFFF' "
    f"-e 'python3 {REMOTE}/scripts/jetson_status_monitor.py'"
)
fire_and_forget(ssh, restart_cmd)
print(">> Blue terminal restarted (background).")

# Quick sanity check — make sure nvidia-smi works
out2, _ = run(ssh, "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits")
print(f"\n>> nvidia-smi GPU check: {out2 or 'FAILED'}")

ssh.close()
print("\n[OK] Done — check the blue terminal on the Jetson screen.")
