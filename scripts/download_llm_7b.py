#!/usr/bin/env python3
"""
MIA_JETSON - Download LLM Models Script
Downloads on the Jetson via SSH:
  1. Qwen 2.5 7B Instruct Q4_K_M  (~4.7 GB)  → models/llm/
  2. Phi-3.5 Mini Instruct Q4_K_M  (~2.4 GB)  → models/llm/

Run this script from your Windows PC:
    python scripts/download_llm_7b.py

It will SSH into the Jetson and run wget with a progress bar.
"""
import subprocess
import sys
import os

# ── SSH target ──────────────────────────────────────────────────────────────
JETSON_HOST = "10.0.0.9"
JETSON_USER = "mia"
JETSON_BASE = "/home/mia/MIA_JETSON"
MODELS_DIR  = f"{JETSON_BASE}/models/llm"

# ── Model URLs (HuggingFace) ─────────────────────────────────────────────────
MODELS = [
    {
        "name": "Qwen 2.5 7B Instruct Q4_K_M",
        "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
        "size_gb": 4.7,
    },
    {
        "name": "Phi-3.5 Mini Instruct Q4_K_M",
        "filename": "phi-3.5-mini-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf",
        "size_gb": 2.4,
    },
]


def run_ssh(cmd: str, desc: str = "") -> int:
    """Run a command on the Jetson via SSH."""
    full_cmd = ["ssh", f"{JETSON_USER}@{JETSON_HOST}", cmd]
    if desc:
        print(f"\n{'='*60}")
        print(f"  {desc}")
        print(f"{'='*60}")
    print(f"[SSH] {cmd}")
    result = subprocess.run(full_cmd, text=True)
    return result.returncode


def download_model(model: dict) -> bool:
    """Download a single model to the Jetson."""
    name     = model["name"]
    filename = model["filename"]
    url      = model["url"]
    dest     = f"{MODELS_DIR}/{filename}"
    size_gb  = model["size_gb"]

    print(f"\n>>> Downloading: {name} (~{size_gb:.1f} GB)")

    # Check if already exists
    check_cmd = f"test -f {dest} && echo EXISTS || echo MISSING"
    result = subprocess.run(
        ["ssh", f"{JETSON_USER}@{JETSON_HOST}", check_cmd],
        capture_output=True, text=True
    )
    if "EXISTS" in result.stdout:
        print(f"    [SKIP] {filename} already exists on Jetson.")
        return True

    # Download with wget (shows progress)
    wget_cmd = (
        f"mkdir -p {MODELS_DIR} && "
        f"wget --show-progress -q -c "
        f"-O {dest} "
        f"'{url}'"
    )
    rc = run_ssh(wget_cmd, f"Downloading {name}")
    if rc == 0:
        print(f"    [OK] {filename} downloaded successfully.")
        return True
    else:
        print(f"    [ERROR] Download failed for {filename} (exit code {rc}).")
        # Clean up partial file
        run_ssh(f"rm -f {dest}", "Cleaning up partial file")
        return False


def verify_disk_space() -> bool:
    """Check that the Jetson has enough free disk space (>10GB)."""
    cmd = "df -BG /home | awk 'NR==2 {gsub(\"G\",\"\",$4); print $4}'"
    result = subprocess.run(
        ["ssh", f"{JETSON_USER}@{JETSON_HOST}", cmd],
        capture_output=True, text=True
    )
    try:
        free_gb = int(result.stdout.strip())
        print(f"[Disk] Free space on Jetson: {free_gb} GB")
        if free_gb < 10:
            print(f"[ERROR] Not enough disk space! Need ≥10GB, found {free_gb}GB.")
            return False
        return True
    except Exception:
        print("[Warning] Could not verify disk space, proceeding anyway...")
        return True


def main():
    print("=" * 60)
    print("  MIA JETSON — LLM Model Downloader")
    print("  Target:", f"{JETSON_USER}@{JETSON_HOST}")
    print("=" * 60)

    # Verify connectivity
    ping = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", f"{JETSON_USER}@{JETSON_HOST}", "echo OK"],
        capture_output=True, text=True
    )
    if "OK" not in ping.stdout:
        print("[ERROR] Cannot connect to Jetson at", JETSON_HOST)
        print("  Make sure the Jetson is on and SSH is running.")
        sys.exit(1)
    print("[OK] Connected to Jetson.")

    # Check disk
    if not verify_disk_space():
        sys.exit(1)

    # Download all models
    total = len(MODELS)
    success = 0
    for i, model in enumerate(MODELS, 1):
        print(f"\n[{i}/{total}] {model['name']}")
        if download_model(model):
            success += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"  Download complete: {success}/{total} models OK")
    print(f"{'='*60}")

    if success == total:
        print("\n[INFO] Both models downloaded. Next step:")
        print("  Run MIA_DEPLOY.bat to push code and restart the service.")
    else:
        print("\n[WARNING] Some downloads failed. Check your internet connection on the Jetson.")
        sys.exit(1)


if __name__ == "__main__":
    main()
