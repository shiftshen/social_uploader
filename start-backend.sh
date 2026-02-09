#!/bin/bash

# SAU Backend Only Starter (macOS/Linux)

# Optional: Conda environment name (if you use Conda)
CONDA_ENV_NAME="social-auto-upload"

echo "=================================================="
echo "  Starting social-auto-upload Backend (port 5409)"
echo "=================================================="
echo ""

# Clean port for a fresh start
if command -v npx &> /dev/null; then
  npx kill-port 5409 || true
else
  if command -v lsof &> /dev/null; then
    lsof -ti:5409 | xargs kill -9 2>/dev/null || true
  fi
fi

echo "[env] Prefer Conda if available; fallback to .venv or system Python"
USE_CONDA=0
if command -v conda &> /dev/null; then
  USE_CONDA=1
fi

echo "[1/1] Starting Python Backend Server in a new terminal..."

# Detect if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use osascript to open a new Terminal window
    if [ "$USE_CONDA" = "1" ]; then
      osascript <<EOF
tell application "Terminal"
    do script "cd \"$PWD\" && conda activate $CONDA_ENV_NAME && python sau_backend.py"
    activate
end tell
EOF
    else
      osascript <<EOF
tell application "Terminal"
    do script "cd \"$PWD\" && if [ -d .venv ]; then source .venv/bin/activate; fi; python sau_backend.py"
    activate
end tell
EOF
    fi
else
    # Linux - try common terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        if [ "$USE_CONDA" = "1" ]; then
          gnome-terminal -- bash -c "conda activate $CONDA_ENV_NAME && python sau_backend.py; exec bash"
        else
          gnome-terminal -- bash -c "cd \"$PWD\" && if [ -d .venv ]; then source .venv/bin/activate; fi; python sau_backend.py; exec bash"
        fi
    elif command -v xterm &> /dev/null; then
        if [ "$USE_CONDA" = "1" ]; then
          xterm -hold -e "conda activate $CONDA_ENV_NAME && python sau_backend.py" &
        else
          xterm -hold -e "bash -lc 'cd "$PWD" && if [ -d .venv ]; then source .venv/bin/activate; fi; python sau_backend.py'" &
        fi
    else
        echo "[WARNING] Could not find a terminal emulator. Running in current terminal..."
        if [ "$USE_CONDA" = "1" ]; then
          conda activate "$CONDA_ENV_NAME"
        elif [ -d .venv ]; then
          # shellcheck disable=SC1091
          source .venv/bin/activate
        fi
        python sau_backend.py
    fi
fi

echo ""
echo "Backend window launched. Monitor logs there and press Ctrl+C to stop."
echo "Tip: If dependencies are missing, activate your environment first (.venv or Conda)."
echo "This launcher will close in 5 seconds..."
sleep 5
