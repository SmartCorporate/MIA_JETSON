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

# Function to position a window exactly by its title using xdotool
position_window() {
    local title="$1"
    local x="$2"
    local y="$3"
    local w="$4"
    local h="$5"
    
    local win_id=""
    for i in {1..25}; do
        win_id=$(DISPLAY=:0 xdotool search --name "$title" 2>/dev/null | tail -n 1)
        if [ -n "$win_id" ]; then
            break
        fi
        sleep 0.2
    done
    
    if [ -n "$win_id" ]; then
        DISPLAY=:0 xdotool windowmove "$win_id" "$x" "$y"
        DISPLAY=:0 xdotool windowsize "$win_id" "$w" "$h"
        # Dual-Lock: Re-apply 0.8s later in background to cancel out window manager shifts or decorations!
        (
            sleep 0.8
            DISPLAY=:0 xdotool windowmove "$win_id" "$x" "$y"
            DISPLAY=:0 xdotool windowsize "$win_id" "$w" "$h"
        ) &
        echo "Snapping '$title' -> pos:(${x}, ${y}) size:(${w}x${h})"
    else
        echo "Warning: Window '$title' not found on desktop"
    fi
}

# 1. GREEN: Main MIA Process
# stdout is written to mia.log and displayed.
# stderr (llama.cpp verbose) → filtered: only real ERRORS go to error.log in real-time.
xterm -title 'MIA - LIVE RUN' \
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

sleep 0.2

# 2. CYAN: System Status Monitor
xterm -title 'MIA - SYSTEM STATUS' \
      -fa 'Monospace' -fs 10 \
      -bg black -fg '#00FFFF' \
      -e "python3 /home/mia/MIA_JETSON/scripts/jetson_status_monitor.py" &

sleep 0.2

# 3. YELLOW: Live log (INFO only, no llama.cpp noise)
xterm -title 'MIA - LIVE LOG' \
      -fa 'Monospace' -fs 9 \
      -bg black -fg '#FFFF00' \
      -e bash -c '
        tail -f /home/mia/MIA_JETSON/mia.log 2>/dev/null \
          | grep --line-buffered -v -E "llama_|ggml_|sched_|graph_|create_tensor|done_getting" \
          || echo "Waiting for log..."
      ' &

sleep 0.2

# 4. RED: Real errors only (filtered — no llama verbose spam)
xterm -title 'MIA - ERRORS' \
      -fa 'Monospace' -fs 9 \
      -bg black -fg '#FF0000' \
      -e bash -c '
        echo "=== MIA ERROR LOG ===";
        tail -f /home/mia/MIA_JETSON/error.log 2>/dev/null \
          || echo "No errors yet."
      ' &

# ── Dynamic snapping to your exact layout ───────────────────────────────────
echo "Snapping windows to your layout..."
position_window "MIA - ERRORS" 99 125 690 124
position_window "MIA - LIVE LOG" 99 303 690 394
position_window "MIA - LIVE RUN" 98 746 697 202
position_window "MIA - SYSTEM STATUS" 97 1001 532 310

echo "Dashboard launched successfully."
