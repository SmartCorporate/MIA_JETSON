#!/usr/bin/env python3
import os
import json
import time
import subprocess
import socket

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Disconnesso"

def get_wifi_status():
    try:
        res = subprocess.check_output("nmcli -t -f WIFI g", shell=True).decode().strip()
        return "ON" if "enabled" in res else "OFF"
    except:
        return "N/D"

def get_ssd_usage():
    try:
        res = subprocess.check_output("df -h / | tail -1", shell=True).decode().split()
        return res[4]
    except:
        return "N/D"

def get_ram_swap():
    try:
        res = subprocess.check_output("free -m", shell=True).decode().split('\n')
        mem = res[1].split()
        swap = res[2].split()
        ram_pct = (int(mem[2]) / int(mem[1])) * 100
        swap_pct = (int(swap[2]) / int(swap[1])) * 100 if int(swap[1]) > 0 else 0
        return ram_pct, swap_pct
    except:
        return 0, 0

def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read().strip()) / 1000.0
        return temp
    except:
        return 0

def get_uptime():
    try:
        res = subprocess.check_output("uptime -p", shell=True).decode().replace('up ', '').strip()
        return res
    except:
        return "N/D"

def get_cpu_gpu_usage():
    cpu = 0
    gpu = 0
    try:
        res = subprocess.check_output("top -bn1 | grep 'Cpu(s)'", shell=True).decode()
        cpu = 100 - float(res.split()[7].replace(',', '.'))
        with open("/sys/devices/gpu.0/load", "r") as f:
            gpu = float(f.read().strip()) / 10.0
    except:
        pass
    return cpu, gpu

def get_models_status():
    config_path = "/home/mia/MIA_JETSON/configs/llm_config.json"
    results = []
    if not os.path.exists(config_path):
        return [("N/A", "Config non trovata")]
    try:
        with open(config_path, 'r') as f:
            cfg = json.load(f)
        models = cfg.get("models", {})
        for key in ["qwen_smart", "qwen_fast", "phi"]:
            if key in models:
                path = os.path.join("/home/mia/MIA_JETSON", models[key].get("path", ""))
                status = "PRONTO" if os.path.exists(path) else "DOWNLOAD"
                results.append((models[key].get("name", key), status))
    except:
        results.append(("Errore", "Lettura fallita"))
    return results

def main():
    while True:
        os.system('clear')
        cpu, gpu = get_cpu_gpu_usage()
        ram, swap = get_ram_swap()
        temp = get_temp()
        uptime = get_uptime()
        wifi = get_wifi_status()
        ssd = get_ssd_usage()
        models = get_models_status()
        
        # MODELLO ATTIVO
        active_model = "Caricamento..."
        if os.path.exists("/tmp/mia_active_model"):
            try:
                with open("/tmp/mia_active_model", "r") as f:
                    active_model = f.read().strip()
            except: pass
            
        print("====================================================")
        print("             MIA JETSON - LIVE MONITOR")
        print("====================================================")
        print(f" MODELLO ATTIVO: {active_model}")
        print("----------------------------------------------------")
        print(f" UPTIME:    {uptime:<25} TEMP: {temp:.1f}°C")
        print(f" WIFI:      {wifi:<25} SSD: {ssd}")
        print(f" IP:        {get_ip()}")
        print("----------------------------------------------------")
        print(" RISORSE SISTEMA:")
        print(f" CPU: {cpu:>5.1f}%   |   RAM:  {ram:>5.1f}%")
        print(f" GPU: {gpu:>5.1f}%   |   SWAP: {swap:>5.1f}%")
        print("----------------------------------------------------")
        print(" DISPONIBILITA MODELLI:")
        for name, status in models:
            print(f" > {name:<25} [{status}]")
        print("====================================================")
        print(" (Refresh 5s)")
        time.sleep(5)

if __name__ == "__main__":
    main()
