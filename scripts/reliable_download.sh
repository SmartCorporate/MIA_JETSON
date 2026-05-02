#!/bin/bash
# MIA - Reliable Model Downloader (DEBUG MODE)
set -e

MODEL_DIR="/home/mia/MIA_JETSON/models/llm"
mkdir -p "$MODEL_DIR"
DEST="$MODEL_DIR/QWEN_7B_SMART.gguf"

echo "=== DIAGNOSTICA DOWNLOAD ==="
echo "Destinazione: $DEST"
rm -f "$DEST"

echo "Verifica connessione a HuggingFace..."
ping -c 1 huggingface.co || echo "ERRORE: Impossibile pingare huggingface.co"

echo "Avvio download con curl (follow redirects)..."
# Usiamo curl con link diretto e ?download=true
URL="https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf?download=true"

curl -L -v -o "$DEST" "$URL" 2>&1 | tee /home/mia/MIA_JETSON/logs/curl_debug.log

echo "Verifica file..."
if [ -f "$DEST" ] && [ $(stat -c%s "$DEST") -gt 1000000 ]; then
    echo "=========================================="
    echo " DOWNLOAD COMPLETATO CON SUCCESSO!"
    echo "=========================================="
else
    echo "ERRORE: Download fallito. Controlla /home/mia/MIA_JETSON/logs/curl_debug.log"
fi
read -p "Premi INVIO..."
