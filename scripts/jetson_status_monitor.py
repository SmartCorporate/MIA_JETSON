#!/usr/bin/env python3
"""
MIA JETSON - LIVE SYSTEM STATUS MONITOR
Blue terminal window — all output in American English.
GPU data sourced from tegrastats (Jetson Orin native).
"""
import os
import json
import time
import subprocess
import socket
import re
from datetime import datetime

BASE = "/home/mia/MIA_JETSON"
CFG  = f"{BASE}/configs/llm_config.json"
W    = 64  # display width

# Jetson Orin GPU sysfs path
GPU_LOAD_PATH = "/sys/devices/platform/bus@0/17000000.gpu/load"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Offline"


# ─────────────────────────────────────────────────────────────
# GPU — Jetson Orin via tegrastats (one-shot) + sysfs
# ─────────────────────────────────────────────────────────────

def get_gpu_data():
    """
    Returns dict: util(%), mem_used_mb, mem_total_mb, gpu_temp_c
    Reads from tegrastats (one shot) for RAM totals and GPU freq,
    plus sysfs for GPU load %.
    """
    info = {"util": 0.0, "mem_used": 0, "mem_total": 0,
            "gpu_temp": 0.0, "cpu_temp": 0.0}
    try:
        # GPU load % from sysfs (0-1000 scale → /10.0 = %)
        try:
            with open(GPU_LOAD_PATH) as f:
                raw = f.read().strip()
                info["util"] = float(raw) / 10.0
        except Exception:
            pass

        # tegrastats single sample for temps and RAM
        ts = _run("timeout 2 tegrastats 2>/dev/null | head -1", timeout=4)
        if ts:
            # RAM used/total e.g. "RAM 2003/7607MB"
            m = re.search(r"RAM\s+(\d+)/(\d+)MB", ts)
            if m:
                info["mem_used"]  = int(m.group(1))
                info["mem_total"] = int(m.group(2))

            # GPU temp e.g. "gpu@47.25C"
            m = re.search(r"gpu@([\d.]+)C", ts)
            if m:
                info["gpu_temp"] = float(m.group(1))

            # CPU temp e.g. "cpu@47.28C" or "tj@47.28C"
            m = re.search(r"cpu@([\d.]+)C", ts)
            if m:
                info["cpu_temp"] = float(m.group(1))
            else:
                m = re.search(r"tj@([\d.]+)C", ts)
                if m:
                    info["cpu_temp"] = float(m.group(1))

    except Exception:
        pass
    return info


# ─────────────────────────────────────────────────────────────
# System data
# ─────────────────────────────────────────────────────────────

def get_sys_data():
    d = {"cpu": 0.0, "ram": 0.0, "swap": 0.0, "ssd": 0.0,
         "uptime": "N/A", "wifi": "?"}
    try:
        # CPU %
        raw = _run("top -bn1 | grep 'Cpu(s)'")
        if raw:
            try:
                # "Cpu(s): 6.2 us, 1.4 sy, 0.0 ni, 92.4 id, ..."
                # idle is field[7] in older top, or parse 'id' explicitly
                m = re.search(r"(\d+[\.,]\d+)\s+id", raw)
                if m:
                    d["cpu"] = 100.0 - float(m.group(1).replace(",", "."))
                else:
                    d["cpu"] = 100.0 - float(raw.split()[7].replace(",", "."))
            except Exception:
                pass

        # RAM / SWAP from free -m
        mem_lines = _run("free -m").split("\n")
        if len(mem_lines) >= 2:
            m = mem_lines[1].split()
            if len(m) >= 3 and int(m[1]) > 0:
                d["ram"] = (int(m[2]) / int(m[1])) * 100.0
        if len(mem_lines) >= 3:
            s = mem_lines[2].split()
            if len(s) >= 3 and int(s[1]) > 0:
                d["swap"] = (int(s[2]) / int(s[1])) * 100.0

        # Disk
        df_out = _run("df / | tail -1").split()
        if df_out:
            d["ssd"] = float(df_out[4].replace("%", ""))

        # Uptime
        up = _run("uptime -p").replace("up ", "").strip()
        d["uptime"] = up[:22] if up else "N/A"

        # WiFi
        wf = _run("nmcli -t -f WIFI g")
        d["wifi"] = "ON" if "enabled" in wf.lower() else "OFF"

    except Exception:
        pass
    return d


# ─────────────────────────────────────────────────────────────
# Active model info
# ─────────────────────────────────────────────────────────────

def get_active_model():
    """Returns (model_display_name, engine_tag) e.g. ('Qwen 7B (Smart)', '[GPU]')"""
    if os.path.exists("/tmp/mia_active_model"):
        try:
            with open("/tmp/mia_active_model") as f:
                content = f.read().strip()
            if " [" in content:
                name, tag = content.rsplit(" [", 1)
                return name.strip(), "[" + tag
            return content, "[GPU]"
        except Exception:
            pass
    return "", ""


def get_models_config():
    try:
        with open(CFG) as f:
            return json.load(f).get("models", {})
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────

BAR_W = 26


def bar(label, pct, width=BAR_W, suffix=""):
    pct = min(max(pct, 0.0), 100.0)
    filled = int((pct / 100.0) * width)
    b = "#" * filled + "-" * (width - filled)
    right = suffix if suffix else f"{pct:5.1f}%"
    return f"{label:<5}[{b}] {right}"


def section(title):
    inner = f"  {title}  "
    pad   = W - len(inner)
    l     = pad // 2
    r     = pad - l
    return "-" * l + inner + "-" * r


def divider(char="="):
    return char * W


def header(title):
    inner = f" {title} "
    pad   = W - len(inner)
    l     = pad // 2
    r     = pad - l
    return "=" * l + inner + "=" * r


# ─────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────

def main():
    os.system("clear")
    while True:
        now    = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        d      = get_sys_data()
        gpu    = get_gpu_data()
        ip     = get_ip()
        active_name, active_tag = get_active_model()
        models = get_models_config()

        # RAM from tegrastats is more accurate on Jetson (unified memory)
        if gpu["mem_total"] > 0:
            vram_pct = (gpu["mem_used"] / gpu["mem_total"]) * 100.0
            vram_sfx = f"{gpu['mem_used']:>5} / {gpu['mem_total']} MB"
        else:
            vram_pct = d["ram"]
            vram_sfx = "N/A"

        gpu_sfx  = f"{gpu['util']:5.1f}%"
        cpu_temp = gpu["cpu_temp"] if gpu["cpu_temp"] > 0 else 0.0
        gpu_temp = gpu["gpu_temp"]

        lines = ["\033[H"]  # cursor home

        lines.append(header("MIA JETSON  —  LIVE STATUS"))
        lines.append(f"  Date  : {now:<{W-12}}")
        lines.append(f"  IP    : {ip:<20}   WiFi: {d['wifi']}   Up: {d['uptime']}")
        lines.append(divider("-"))

        # ── Hardware Metrics ─────────────────────────────────
        lines.append(section("HARDWARE"))
        lines.append(f"  {bar('CPU  ', d['cpu'])}   Temp: {cpu_temp:.1f} C")
        lines.append(f"  {bar('GPU  ', gpu['util'], suffix=gpu_sfx)}   Temp: {gpu_temp:.1f} C")
        lines.append(f"  {bar('MEM  ', vram_pct,   suffix=vram_sfx)}")
        lines.append(f"  {bar('SWAP ', d['swap'])}")
        lines.append(f"  {bar('DISK ', d['ssd'])}")
        lines.append(divider("-"))

        # ── AI MODEL USED ────────────────────────────────────
        lines.append(section("AI MODEL USED"))
        if models:
            for m_id, m_info in models.items():
                name       = m_info.get("name", m_id)
                gpu_layers = m_info.get("n_gpu_layers", 0)
                is_active  = (name == active_name)

                # Engine label
                if is_active and active_tag:
                    eng = active_tag
                elif gpu_layers != 0:
                    eng = "[GPU]"
                else:
                    eng = "[CPU]"

                if is_active:
                    marker = ">> RUNNING"
                    line   = f"  {marker} {eng}  {name}"
                else:
                    line   = f"     STANDBY {eng}  {name}"

                lines.append(line)
        else:
            lines.append("  No models configured.")

        lines.append(divider())

        # Pad lines and print
        out_lines = []
        for ln in lines:
            if ln.startswith("\033"):
                out_lines.append(ln)
            else:
                out_lines.append(ln.ljust(W)[:W])

        print("\n".join(out_lines), flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
