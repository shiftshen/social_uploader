#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/new"
EXTERNAL_DRIVE_PATH="/Volumes/M2USB"
DOCKER_DATA_DIR="$EXTERNAL_DRIVE_PATH/Docker"

echo "Restoring Social Uploader Services..."

SETTINGS_STORE="$HOME/Library/Group Containers/group.com.docker/settings-store.json"
INTERNAL_DATA_FOLDER="$HOME/Library/Containers/com.docker.docker/Data"

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not reachable. Attempting to recover Docker Desktop settings..."
    if [ -f "$SETTINGS_STORE" ]; then
        TS="$(date '+%Y%m%d_%H%M%S')"
        cp "$SETTINGS_STORE" "$SETTINGS_STORE.bak.$TS"
        python3 - <<PY
import json, os
p = os.path.expanduser("$SETTINGS_STORE")
with open(p, "r", encoding="utf-8") as f:
    d = json.load(f)
d["DataFolder"] = os.path.expanduser("$INTERNAL_DATA_FOLDER")
with open(p, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
PY
        echo "Updated DataFolder to internal default: $INTERNAL_DATA_FOLDER"
        echo "Backup saved as: $SETTINGS_STORE.bak.$TS"
    else
        echo "settings-store.json not found at: $SETTINGS_STORE"
    fi
    echo "Starting Docker Desktop..."
    open -a Docker
    echo "Wait for Docker to start, then re-run: ./restore.sh"
    exit 0
fi

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "Error: Project directory not found."
    exit 1
fi

DOCKER_INTERNAL_RAW="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
DOCKER_INTERNAL_QCOW2="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.qcow2"
DOCKER_EXTERNAL_RAW="$DOCKER_DATA_DIR/Docker.raw"
DOCKER_EXTERNAL_QCOW2="$DOCKER_DATA_DIR/Docker.qcow2"

if [ ! -f "$DOCKER_EXTERNAL_RAW" ] && [ ! -f "$DOCKER_EXTERNAL_QCOW2" ]; then
    if [ -f "$DOCKER_INTERNAL_RAW" ] || [ -f "$DOCKER_INTERNAL_QCOW2" ]; then
        echo "WARN: Docker disk image is currently on internal disk."
        echo "Move Docker Desktop Disk image location to: $DOCKER_DATA_DIR"
        echo "Docker Desktop -> Settings -> Resources -> Disk image location -> Apply & Restart"
    fi
fi

cd "$PROJECT_ROOT"

echo "Stopping existing containers..."
docker-compose down

echo "Cleaning up AppleDouble files..."
find . -name "._*" -delete

echo "Pulling/Building images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Done! Services should be running."
echo "Frontend: http://localhost:5106"
echo "Backend:  http://localhost:5406"
