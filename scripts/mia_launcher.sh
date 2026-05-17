#!/bin/bash
# MIA - Dashboard Launcher (4 colored terminals)
# Error log cleaned: llama.cpp verbose stderr suppressed.

export DISPLAY=:0
export XAUTHORITY=/run/user/1000/gdm/Xauthority
xhost +local:mia > /dev/null 2>&1

# Kill previous sessions cleanly
pkill -f xterm 2>/dev/null
pkill -f "main.py" 2>/dev/null
sleep 1

echo "Launching MIA Dashboard..."

# ── Pre-clear log files so RED terminal starts clean ──────────────────────────
> /home/mia/MIA_JETSON/error.log
> /home/mia/MIA_JETSON/mia.log

# 1. GREEN: Main MIA Process
# stdout is written to mia.log and displayed.
# stderr (llama.cpp verbose) → filtered: only real ERRORS go to error.log in real-time.
xterm -title 'MIA - LIVE RUN' \
      -geometry 110x30+10+10 \
      -fa 'Monospace' -fs 11 \
      -bg black -fg '#00FF00' \
      -e bash -c '
        echo "=== MIA JETSON STARTING ===";
        cd /home/mia/MIA_JETSON;
        python3 -u src/main.py \
          > >(tee -a /home/mia/MIA_JETSON/mia.log) \
          2> >(grep --line-buffered -E "^\[(Brain Error|Orchestrator|Audio Error|STT Error)\]|ERROR|CRITICAL|Traceback|Exception" \
               >> /home/mia/MIA_JETSON/error.log);
        echo "MIA stopped. Press ENTER to close.";
        read
      ' &

sleep 0.5

# 2. CYAN: System Status Monitor
xterm -title 'MIA - SYSTEM STATUS' \
      -geometry 100x32+10+500 \
      -fa 'Monospace' -fs 10 \
      -bg black -fg '#00FFFF' \
      -e "python3 /home/mia/MIA_JETSON/scripts/jetson_status_monitor.py" &

sleep 0.3

# 3. YELLOW: Live log (INFO only, no llama.cpp noise)
xterm -title 'MIA - LIVE LOG' \
      -geometry 90x18+900+10 \
      -fa 'Monospace' -fs 9 \
      -bg black -fg '#FFFF00' \
      -e bash -c '
        tail -f /home/mia/MIA_JETSON/mia.log 2>/dev/null \
          | grep --line-buffered -v -E "llama_|ggml_|sched_|graph_|create_tensor|done_getting" \
          || echo "Waiting for log..."
      ' &

sleep 0.3

# 4. RED: Real errors only (filtered — no llama verbose spam)
xterm -title 'MIA - ERRORS' \
      -geometry 90x18+900+410 \
      -fa 'Monospace' -fs 9 \
      -bg black -fg '#FF0000' \
      -e bash -c '
        echo "=== MIA ERROR LOG ===";
        tail -f /home/mia/MIA_JETSON/error.log 2>/dev/null \
          || echo "No errors yet."
      ' &

echo "Dashboard launched successfully."
