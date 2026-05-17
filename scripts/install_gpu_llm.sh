#!/bin/bash
# MIA - Riparazione e Installazione CUDA (JetPack 6)
set -e

PASS="MIA_JETSON"

echo "===================================================="
echo " MIA JETSON - RIPARAZIONE PACCHETTI CORROTTI"
echo "===================================================="

# 1. Pulizia e Riparazione APT
echo "[1/3] Sblocco e riparazione sistema pacchetti..."
echo "$PASS" | sudo -S dpkg --configure -a
echo "$PASS" | sudo -S apt-get install -f -y
echo "$PASS" | sudo -S apt-get update

# 2. Installazione CUDA specifica
echo "[2/3] Installazione Toolkit CUDA 12..."
echo "$PASS" | sudo -S apt-get install -y cuda-toolkit-12

# Creazione link simbolico se manca
if [ ! -d "/usr/local/cuda" ]; then
    CUDA_PATH=$(find /usr/local -name "cuda-*" -type d | head -n 1)
    if [ -n "$CUDA_PATH" ]; then
        echo "$PASS" | sudo -S ln -s "$CUDA_PATH" /usr/local/cuda
    fi
fi

export CUDA_HOME=/usr/local/cuda
export PATH=$PATH:$CUDA_HOME/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64

echo "Verifica NVCC..."
nvcc --version || (echo "ERRORE: CUDA ancora non trovato." && exit 1)

# 3. Compilazione Motore GPU
echo "[3/3] Compilazione Motore GPU (Forzata)..."
export CMAKE_ARGS="-DLLAMA_CUDA=on"
export FORCE_CMAKE=1
echo "$PASS" | sudo -S pip3 install llama-cpp-python --upgrade --force-reinstall --no-cache-dir --no-build-isolation

echo "===================================================="
echo " MIA PRONTA IN GPU! Avvio..."
echo "===================================================="
cd /home/mia/MIA_JETSON && python3 src/main.py
