#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
EXTERNAL_DRIVE_PATH="/Volumes/M2USB"
DOCKER_DATA_DIR="$EXTERNAL_DRIVE_PATH/Docker"
LOG_FILE="$SCRIPT_DIR/deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Social Uploader Deployment..."

log "Step 1: Checking and Installing Dependencies..."

if ! command -v brew &> /dev/null; then
    log "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    log "Homebrew is already installed."
fi

if ! command -v git &> /dev/null; then
    log "Installing Git..."
    brew install git
else
    log "Git is already installed."
fi

if ! command -v docker &> /dev/null; then
    log "Installing Docker..."
    brew install --cask docker
    log "Please open Docker Desktop to finish installation and wait for it to start."
    read -p "Press Enter after Docker Desktop is running..."
else
    log "Docker is installed."
fi

if ! docker info &> /dev/null; then
    log "Docker is not running. Attempting to start Docker..."
    open -a Docker
    log "Waiting for Docker to start (this may take a minute)..."
    while ! docker info &> /dev/null; do
        sleep 5
        echo -n "."
    done
    echo ""
    log "Docker is running."
fi

if [ ! -d "$DOCKER_DATA_DIR" ]; then
    log "Creating Docker data directory at $DOCKER_DATA_DIR"
    mkdir -p "$DOCKER_DATA_DIR"
fi

DOCKER_INTERNAL_RAW="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
DOCKER_INTERNAL_QCOW2="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.qcow2"
DOCKER_EXTERNAL_RAW_1="$DOCKER_DATA_DIR/Docker.raw"
DOCKER_EXTERNAL_QCOW2_1="$DOCKER_DATA_DIR/Docker.qcow2"
DOCKER_EXTERNAL_RAW_2="$DOCKER_DATA_DIR/Containers/DockerDesktop/Docker.raw"
DOCKER_EXTERNAL_QCOW2_2="$DOCKER_DATA_DIR/Containers/DockerDesktop/Docker.qcow2"

if [ -f "$DOCKER_EXTERNAL_RAW_1" ] || [ -f "$DOCKER_EXTERNAL_QCOW2_1" ] || [ -f "$DOCKER_EXTERNAL_RAW_2" ] || [ -f "$DOCKER_EXTERNAL_QCOW2_2" ]; then
    if [ -f "$DOCKER_EXTERNAL_RAW_2" ]; then
        log "Docker disk image is on external drive: $DOCKER_EXTERNAL_RAW_2"
        ls -lh "$DOCKER_EXTERNAL_RAW_2" | tee -a "$LOG_FILE"
    elif [ -f "$DOCKER_EXTERNAL_QCOW2_2" ]; then
        log "Docker disk image is on external drive: $DOCKER_EXTERNAL_QCOW2_2"
        ls -lh "$DOCKER_EXTERNAL_QCOW2_2" | tee -a "$LOG_FILE"
    elif [ -f "$DOCKER_EXTERNAL_RAW_1" ]; then
        log "Docker disk image is on external drive: $DOCKER_EXTERNAL_RAW_1"
        ls -lh "$DOCKER_EXTERNAL_RAW_1" | tee -a "$LOG_FILE"
    else
        log "Docker disk image is on external drive: $DOCKER_EXTERNAL_QCOW2_1"
        ls -lh "$DOCKER_EXTERNAL_QCOW2_1" | tee -a "$LOG_FILE"
    fi
else
    if [ -f "$DOCKER_INTERNAL_RAW" ] || [ -f "$DOCKER_INTERNAL_QCOW2" ]; then
        log "ERROR: Docker disk image is currently on internal disk."
        if [ -f "$DOCKER_INTERNAL_RAW" ]; then
            ls -lh "$DOCKER_INTERNAL_RAW" | tee -a "$LOG_FILE"
        else
            ls -lh "$DOCKER_INTERNAL_QCOW2" | tee -a "$LOG_FILE"
        fi
        log "Move Docker Desktop Disk image location to: $DOCKER_DATA_DIR"
        log "Docker Desktop -> Settings -> Resources -> Disk image location -> Apply & Restart"
        log "After moving, re-run this script."
        exit 1
    fi
fi

log "=================================================================="
log "IMPORTANT: To ensure Docker uses the external drive for storage:"
log "1. Open Docker Desktop Dashboard"
log "2. Go to Settings -> Resources -> Disk image location"
log "3. Set it to: $DOCKER_DATA_DIR"
log "4. Click Apply & Restart"
log "=================================================================="
log "Note: The application data (database, videos) will be automatically stored in the project directory on the external drive."
log "Waiting 5 seconds for you to read..."
sleep 5

log "Step 2: Configuring Project..."

if [ ! -d "$PROJECT_ROOT" ]; then
    log "Error: Project directory not found at $PROJECT_ROOT"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/conf.py" ]; then
    log "Creating conf.py from example..."
    cp "$PROJECT_ROOT/conf.example.py" "$PROJECT_ROOT/conf.py"
fi

log "Creating data directories..."
mkdir -p "$PROJECT_ROOT/videoFile"
mkdir -p "$PROJECT_ROOT/videos"
mkdir -p "$PROJECT_ROOT/logs"

log "Initializing database..."
cd "$PROJECT_ROOT"
python3 db/createTable.py

log "Step 3: Building and Starting Services..."

log "Cleaning up AppleDouble files..."
find . -name "._*" -delete

log "Building Docker images (this may take a while)..."
docker-compose build

log "Starting services..."
docker-compose up -d

if [ $? -eq 0 ]; then
    log "Services started successfully."
else
    log "Error starting services."
    exit 1
fi

log "Step 4: Configuring System Auto-start..."

PLIST_LABEL="com.socialuploader.start"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
DOCKER_COMPOSE_PATH=$(which docker-compose)

if [ -z "$DOCKER_COMPOSE_PATH" ]; then
    DOCKER_COMPOSE_PATH="/usr/local/bin/docker-compose"
fi

cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${DOCKER_COMPOSE_PATH}</string>
        <string>-f</string>
        <string>${PROJECT_ROOT}/docker-compose.yml</string>
        <string>up</string>
        <string>-d</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>${PROJECT_ROOT}</string>
    <key>StandardOutPath</key>
    <string>${PROJECT_ROOT}/logs/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>${PROJECT_ROOT}/logs/launchd.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

log "Loading LaunchAgent..."
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

log "=================================================================="
log "Deployment Completed Successfully!"
log "Frontend URL: http://localhost:5106"
log "Backend URL: http://localhost:5406"
log "Data Directory: $PROJECT_ROOT"
log "Log File: $LOG_FILE"
log "=================================================================="
