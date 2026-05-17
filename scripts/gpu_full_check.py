#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
MIA JETSON - GPU FULL CHECK & FIX
Verifica e sistema tutto per far girare Qwen 7B su GPU.
Esegue via SSH sul Jetson.
"""
import os
import sys
import time
import paramiko

# ─── SSH CONFIG ────────────────────────────────────────────────────────────────
HOST     = '10.0.0.9'
USER     = 'mia'
PASSWORD = 'MIA_JETSON'
REMOTE   = '/home/mia/MIA_JETSON'

# ─── SCRIPT DA ESEGUIRE SUL JETSON ────────────────────────────────────────────
REMOTE_SCRIPT = r"""
import subprocess, os, sys, json

SEP  = "=" * 60
SEP2 = "-" * 60

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return "", str(e)

print(SEP)
print("  MIA JETSON — GPU FULL DIAGNOSTIC")
print(SEP)

# 1. CUDA / nvcc
print("\n[1] CUDA / NVCC")
out, err = run("nvcc --version 2>&1")
if "release" in out.lower():
    for line in out.splitlines():
        if "release" in line.lower():
            print(f"  ✓ CUDA: {line.strip()}")
else:
    print(f"  ✗ nvcc non trovato: {err or out}")

# 2. nvidia-smi
print("\n[2] NVIDIA-SMI / GPU")
out, _ = run("nvidia-smi 2>&1")
if "NVIDIA" in out or "GeForce" in out or "Orin" in out or "tegra" in out.lower():
    for line in out.splitlines()[:6]:
        print(f"  {line}")
else:
    # Jetson usa tegrastats
    out2, _ = run("tegrastats --interval 1000 &")
    gload, _ = run("cat /sys/devices/gpu.0/load 2>/dev/null || echo N/A")
    print(f"  GPU load (Jetson): {gload}")
    out3, _ = run("cat /sys/bus/platform/drivers/host1x/*/devfreq/*/cur_freq 2>/dev/null | head -1")
    print(f"  GPU freq: {out3 or 'N/A'}")

# 3. llama-cpp-python — check CUBLAS
print("\n[3] llama-cpp-python GPU SUPPORT")
try:
    import llama_cpp
    print(f"  ✓ llama-cpp-python installato: {llama_cpp.__version__}")
    # Verifica se compilato con CUBLAS
    lib_path = os.path.dirname(llama_cpp.__file__)
    so_files, _ = run(f"find {lib_path} -name '*.so' 2>/dev/null")
    cublas_ok = False
    for so in so_files.splitlines():
        out, _ = run(f"strings {so} 2>/dev/null | grep -i cublas | head -1")
        if out:
            cublas_ok = True
            break
    if not cublas_ok:
        # Try ldd
        for so in so_files.splitlines():
            out, _ = run(f"ldd {so} 2>/dev/null | grep -i cuda | head -1")
            if out:
                cublas_ok = True
                break
    if cublas_ok:
        print("  ✓ Compilato con CUBLAS (GPU support)")
    else:
        print("  ✗ NON compilato con CUBLAS — sarà CPU-only!")
        print("  → Serve ricompilare con: CMAKE_ARGS=-DGGML_CUDA=on")
except ImportError:
    print("  ✗ llama-cpp-python NON installato!")

# 4. Modello GGUF
print("\n[4] FILE MODELLO GGUF")
model_path = "/home/mia/MIA_JETSON/models/llm/QWEN_7B_SMART.gguf"
if os.path.exists(model_path):
    size_gb = os.path.getsize(model_path) / (1024**3)
    print(f"  ✓ Trovato: {model_path}")
    print(f"  ✓ Dimensione: {size_gb:.2f} GB")
else:
    print(f"  ✗ NON TROVATO: {model_path}")
    # Cerca GGUF alternativi
    out, _ = run("find /home/mia/MIA_JETSON/models -name '*.gguf' 2>/dev/null")
    if out:
        print("  File GGUF trovati:")
        for f in out.splitlines():
            sz = os.path.getsize(f) / (1024**3) if os.path.exists(f) else 0
            print(f"    {f} ({sz:.2f} GB)")
    else:
        print("  Nessun file .gguf trovato nella cartella models!")

# 5. Test caricamento GPU
print("\n[5] TEST CARICAMENTO GPU (Qwen 7B)")
try:
    from llama_cpp import Llama
    mpath = "/home/mia/MIA_JETSON/models/llm/QWEN_7B_SMART.gguf"
    if not os.path.exists(mpath):
        # Prova fallback
        out, _ = run("find /home/mia/MIA_JETSON/models -name '*.gguf' 2>/dev/null | head -1")
        mpath = out.strip() if out.strip() else None

    if mpath and os.path.exists(mpath):
        print(f"  Caricamento {os.path.basename(mpath)} con n_gpu_layers=-1...")
        llm = Llama(model_path=mpath, n_ctx=512, n_gpu_layers=-1, n_threads=4, verbose=True)
        print("  ✓ Modello caricato! Test risposta rapida...")
        res = llm("Ciao, come stai?", max_tokens=20, stop=["\\n"])
        answer = res['choices'][0]['text'].strip()
        print(f"  ✓ Risposta: {answer}")
        # Controlla se GPU usata
        gload, _ = run("cat /sys/devices/gpu.0/load 2>/dev/null || echo N/A")
        print(f"  GPU load dopo inferenza: {gload}")
    else:
        print("  ✗ Nessun modello disponibile per il test")
except Exception as e:
    print(f"  ✗ Errore: {e}")

print(SEP)
print("  DIAGNOSI COMPLETA")
print(SEP)
"""

def run_ssh_command(ssh, cmd, timeout=120):
    """Esegue un comando SSH e stampa output in real-time."""
    chan = ssh.get_transport().open_session()
    chan.exec_command(cmd)
    output = []
    while True:
        if chan.recv_ready():
            chunk = chan.recv(4096).decode('utf-8', errors='replace')
            print(chunk, end='', flush=True)
            output.append(chunk)
        if chan.recv_stderr_ready():
            chunk = chan.recv_stderr(4096).decode('utf-8', errors='replace')
            print(chunk, end='', flush=True)
            output.append(chunk)
        if chan.exit_status_ready():
            # Drain remaining
            while chan.recv_ready():
                chunk = chan.recv(4096).decode('utf-8', errors='replace')
                print(chunk, end='', flush=True)
                output.append(chunk)
            break
        time.sleep(0.1)
    return ''.join(output), chan.recv_exit_status()


def main():
    print("=" * 60)
    print("  MIA JETSON - GPU CHECK & FIX (da PC)")
    print("=" * 60)
    print(f"\n>> Connessione SSH a {HOST}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=15)
        print("✓ Connesso!\n")
    except Exception as e:
        print(f"ERRORE SSH: {e}")
        sys.exit(1)

    # Carica lo script diagnostico sul Jetson
    sftp = ssh.open_sftp()
    remote_script_path = f"{REMOTE}/scripts/_gpu_diag_run.py"
    with sftp.open(remote_script_path, 'w') as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()
    print(f">> Script caricato su {remote_script_path}\n")

    # Esegui diagnosi
    print("─" * 60)
    print("  AVVIO DIAGNOSI SUL JETSON")
    print("─" * 60)
    out, code = run_ssh_command(ssh, f"cd {REMOTE} && python3 {remote_script_path} 2>&1")
    
    print("\n" + "=" * 60)
    
    # Analisi risultati e fix automatico
    needs_recompile = "NON compilato con CUBLAS" in out or "NON installato" in out
    model_missing = "NON TROVATO" in out and "QWEN_7B_SMART.gguf" in out
    
    if needs_recompile:
        print("\n[!] llama-cpp-python NON ha supporto GPU.")
        print(">> Avvio RICOMPILAZIONE con CUDA...")
        print("-" * 60)
        
        fix_cmd = (
            "export CUDA_HOME=/usr/local/cuda && "
            "export PATH=$PATH:/usr/local/cuda/bin && "
            "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64 && "
            "export CMAKE_ARGS='-DGGML_CUDA=on' && "
            "export FORCE_CMAKE=1 && "
            "pip3 install llama-cpp-python --upgrade --force-reinstall --no-cache-dir --no-build-isolation 2>&1"
        )
        print(f"Comando: {fix_cmd}\n")
        out2, code2 = run_ssh_command(ssh, fix_cmd)
        
        if code2 == 0:
            print("\n✓ Ricompilazione completata!")
        else:
            print(f"\n✗ Ricompilazione fallita (exit code {code2})")
            print("  Prova manuale: ssh mia@10.0.0.9 e segui le istruzioni")
    
    if model_missing:
        print("\n[!] Modello QWEN_7B_SMART.gguf NON trovato!")
        print("  Verifica se il modello deve essere scaricato.")
        # Check modelli disponibili
        out3, _ = run_ssh_command(ssh, f"ls -lah {REMOTE}/models/llm/ 2>&1 || echo 'Cartella vuota o assente'")
    
    if not needs_recompile and not model_missing:
        print("[OK] Sistema OK! GPU e modello pronti.")
        print("\n>> Avvio MIA con launcher multi-terminale...")
        run_ssh_command(ssh, f"bash {REMOTE}/scripts/mia_launcher.sh 2>&1 &")
    
    ssh.close()
    print("\n[OK] Done.")


if __name__ == "__main__":
    main()
