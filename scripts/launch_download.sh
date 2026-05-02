#!/bin/bash
# Wrapper per il download Python
DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority gnome-terminal --title="MIA - DOWNLOAD DEFINITIVO" -- bash -c "python3 /home/mia/MIA_JETSON/scripts/download_via_hf_hub.py; echo 'PREMI INVIO PER CHIUDERE'; read"
