#!/usr/bin/env python3
"""
MIA_JETSON — Service installer + live log monitor
Runs via paramiko (uses password from .env).
After installing the service, opens a live log window on screen.
"""
import os
import sys
import subprocess
import time

try:
    import paramiko
    from dotenv import load_dotenv
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "python-dotenv"])
    import paramiko
    from dotenv import load_dotenv

# ── Load credentials ─────────────────────────────────────────────────────────
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

HOST     = os.getenv('JETSON_IP',       '10.0.0.9')
USER     = os.getenv('JETSON_USER',     'mia')
PASSWORD = os.getenv('JETSON_PASSWORD', 'MIA_JETSON')
BASE     = os.getenv('JETSON_PATH',     '/home/mia/MIA_JETSON')

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=10)
    return ssh

def run(ssh, cmd, desc=""):
    if desc:
        print(f"\n[SSH] {desc}")
    print(f"  $ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    stdin.write(PASSWORD + "\n")
    stdin.flush()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    # Write safely to stdout (handles special unicode chars like ●)
    if out:
        sys.stdout.buffer.write((out + "\n").encode('utf-8', errors='replace'))
        sys.stdout.buffer.flush()
    if err:
        sys.stdout.buffer.write((f"[STDERR] {err}\n").encode('utf-8', errors='replace'))
        sys.stdout.buffer.flush()
    return out

def main():
    print("=" * 60)
    print("  MIA JETSON — Service Setup + Live Monitor")
    print("=" * 60)

    ssh = ssh_connect()
    print(f"[OK] Connesso a {USER}@{HOST}")

    # 1. Install updated service file
    run(ssh,
        f"sudo cp {BASE}/mia_jetson.service /etc/systemd/system/mia_jetson.service",
        "Installazione service file")

    # 2. Reload systemd
    run(ssh, "sudo systemctl daemon-reload", "Reload systemd")

    # 3. Restart MIA
    run(ssh, "sudo systemctl restart mia_jetson", "Restart MIA_JETSON")
    time.sleep(2)

    # 4. Check status
    run(ssh, "sudo systemctl status mia_jetson --no-pager -l", "Status servizio")

    ssh.close()
    print("\n" + "=" * 60)
    print("  Apro terminale con log live sulla Jetson...")
    print("=" * 60)

    # 5. Open a new PowerShell window that SSH's into Jetson and tails logs live
    #    We open a persistent SSH session that runs journalctl -f
    log_script = (
        "$host.UI.RawUI.WindowTitle = 'MIA JETSON - LOG LIVE'; "
        "Write-Host '=== MIA JETSON LOG IN TEMPO REALE ===' -ForegroundColor Green; "
        f"ssh -o StrictHostKeyChecking=no -o PasswordAuthentication=yes "
        f"-t {USER}@{HOST} "
        f"'echo {PASSWORD} | sudo -S journalctl -u mia_jetson -f --no-pager -n 80 --output=cat'"
    )
    subprocess.Popen(
        ["powershell", "-NoExit", "-Command", log_script],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    print("[OK] Finestra log aperta sulla Jetson!")

if __name__ == "__main__":
    main()
