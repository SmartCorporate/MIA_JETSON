#!/usr/bin/env python3
"""
MIA_JETSON — Apre un terminale con log live SUL DISPLAY della Jetson.
Il terminale compare fisicamente sullo schermo connesso alla Jetson, non qui.
"""
import subprocess
import sys
import os

try:
    import paramiko
    from dotenv import load_dotenv
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "python-dotenv"])
    import paramiko
    from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

HOST     = os.getenv('JETSON_IP',       '10.0.0.9')
USER     = os.getenv('JETSON_USER',     'mia')
PASSWORD = os.getenv('JETSON_PASSWORD', 'MIA_JETSON')

def ssh_run(ssh, cmd, use_sudo=False):
    """Run command on Jetson. use_sudo=True pipes password for sudo."""
    print(f"[Jetson] $ {cmd}")
    if use_sudo:
        full_cmd = f"echo '{PASSWORD}' | sudo -S {cmd}"
        stdin, stdout, stderr = ssh.exec_command(full_cmd)
    else:
        stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    if out:
        sys.stdout.buffer.write((out + "\n").encode('utf-8', errors='replace'))
        sys.stdout.buffer.flush()
    return out

def main():
    print(f"Connessione a {USER}@{HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=10)
    print("[OK] Connesso.\n")

    # Il comando da eseguire nel terminale sulla Jetson
    log_cmd = f"echo {PASSWORD} | sudo -S journalctl -u mia_jetson -f --no-pager -n 100"

    # Prova terminali comuni su Ubuntu/Jetson, sul display fisico :0
    terminals = [
        # gnome-terminal (Ubuntu default)
        f"DISPLAY=:0 XAUTHORITY=/home/{USER}/.Xauthority gnome-terminal --title='MIA LOG LIVE' -- bash -c '{log_cmd}; read'",
        # xterm (molto comune, leggero)
        f"DISPLAY=:0 XAUTHORITY=/home/{USER}/.Xauthority xterm -title 'MIA LOG LIVE' -e 'bash -c \"{log_cmd}; read\"' &",
        # lxterminal (LXDE)
        f"DISPLAY=:0 XAUTHORITY=/home/{USER}/.Xauthority lxterminal --title='MIA LOG LIVE' -e 'bash -c \"{log_cmd}; read\"' &",
        # xfce4-terminal
        f"DISPLAY=:0 XAUTHORITY=/home/{USER}/.Xauthority xfce4-terminal --title='MIA LOG LIVE' -e 'bash -c \"{log_cmd}; read\"' &",
    ]

    # Rileva terminale disponibile (senza sudo, no pty — output pulito)
    stdin, stdout, _ = ssh.exec_command(
        "which gnome-terminal 2>/dev/null || which xterm 2>/dev/null || "
        "which lxterminal 2>/dev/null || which xfce4-terminal 2>/dev/null || echo NONE"
    )
    available = stdout.read().decode('utf-8', errors='replace').strip().split('\n')[0].strip()
    print(f"[INFO] Terminale trovato sulla Jetson: {available}")

    if available == "NONE" or not available:
        print("[INFO] xterm non trovato, lo installo...")
        ssh_run(ssh, "apt-get install -y xterm", use_sudo=True)
        available = "/usr/bin/xterm"

    term_name = os.path.basename(available)
    display_prefix = f"DISPLAY=:0 XAUTHORITY=/home/{USER}/.Xauthority"

    # Costruisci il comando di apertura terminale
    if "gnome-terminal" in term_name:
        open_cmd = (
            f"{display_prefix} nohup gnome-terminal "
            f"--title='MIA LOG LIVE' -- bash -c '{log_cmd}; exec bash' "
            f">/tmp/mia_term.log 2>&1 &"
        )
    elif "xterm" in term_name:
        open_cmd = (
            f"{display_prefix} nohup xterm "
            f"-fa 'Monospace' -fs 11 -bg black -fg lime "
            f"-title 'MIA LOG LIVE' "
            f"-e bash -c '{log_cmd}; exec bash' "
            f">/tmp/mia_term.log 2>&1 &"
        )
    elif "lxterminal" in term_name:
        open_cmd = (
            f"{display_prefix} nohup lxterminal "
            f"--title='MIA LOG LIVE' "
            f"-e \"bash -c '{log_cmd}; exec bash'\" "
            f">/tmp/mia_term.log 2>&1 &"
        )
    else:  # xfce4-terminal
        open_cmd = (
            f"{display_prefix} nohup xfce4-terminal "
            f"--title='MIA LOG LIVE' "
            f"-e \"bash -c '{log_cmd}; exec bash'\" "
            f">/tmp/mia_term.log 2>&1 &"
        )

    print(f"\n[Apertura {term_name} sul display della Jetson...]")
    ssh_run(ssh, open_cmd)

    import time
    time.sleep(2)
    print(f"\n[OK] Il terminale '{term_name}' è stato avviato sullo schermo della Jetson.")
    ssh.close()

if __name__ == "__main__":
    main()
