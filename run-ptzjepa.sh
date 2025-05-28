#!/bin/bash

CONFIG_FILE=${1:-"./configs/Config_file.yaml"}

# Extract values from config file using python3
EXTRACT_CMD=$(cat <<EOF
import yaml
import sys

with open("$CONFIG_FILE", "r") as f:
    config = yaml.safe_load(f)

dep = config.get("deployment", {})
camera = dep.get("camera", {})
operation = dep.get("operation", {})
distributed = dep.get("distributed", {})
docker = dep.get("docker", {})

print(f"""
CAMERA_IP={camera.get('ip', '')}
CAMERA_USERNAME={camera.get('username', '')}
CAMERA_PASSWORD={camera.get('password', '')}
CAMERA_BRAND={camera.get('brand', 0)}
RUN_MODE={operation.get('run_mode', 'lifelong')}
ITERATIONS={operation.get('iterations', 20)}
MOVEMENTS={operation.get('movements', 20)}
DEBUG={'true' if operation.get('debug', False) else 'false'}
TRACK_POSITIONS={'true' if operation.get('track_positions', False) else 'false'}
TRACK_ALL={'true' if operation.get('track_all', False) else 'false'}
KEEP_IMAGES={'true' if operation.get('keep_images', False) else 'false'}
DISTRIBUTED={'true' if distributed.get('enabled', False) else 'false'}
DISTRIBUTED_IP={distributed.get('ip', '')}
DISTRIBUTED_USERNAME={distributed.get('username', '')}
DISTRIBUTED_DIR={distributed.get('directory', '')}
DOCKER_IMAGE={docker.get('image', 'ptzjepa:latest')}
PERSISTENCE_PATH={docker.get('persistence_path', '/persistence')}
APP_PATH={docker.get('app_path', '/app')}
LOG_PATH={docker.get('log_path', '/logs/ptzjepa.log')}
""")
EOF
)

# Load config values into environment
eval "$(python3 -c "$EXTRACT_CMD")"

# Build the command arguments
ARGS=""
[[ -n "$CAMERA_IP" ]] && ARGS="$ARGS -ip $CAMERA_IP"
[[ -n "$CAMERA_USERNAME" ]] && ARGS="$ARGS -un $CAMERA_USERNAME"
[[ -n "$CAMERA_PASSWORD" ]] && ARGS="$ARGS -pw $CAMERA_PASSWORD"
[[ -n "$CAMERA_BRAND" ]] && ARGS="$ARGS -cb $CAMERA_BRAND"
[[ -n "$RUN_MODE" ]] && ARGS="$ARGS -rm $RUN_MODE"
[[ -n "$ITERATIONS" ]] && ARGS="$ARGS -it $ITERATIONS"
[[ -n "$MOVEMENTS" ]] && ARGS="$ARGS -mv $MOVEMENTS"
[[ "$DEBUG" == "true" ]] && ARGS="$ARGS --debug"
[[ "$TRACK_POSITIONS" == "true" ]] && ARGS="$ARGS -tp"
[[ "$KEEP_IMAGES" == "true" ]] && ARGS="$ARGS -ki"
[[ "$TRACK_ALL" == "true" ]] && ARGS="$ARGS --track_all"

if [[ "$DISTRIBUTED" == "true" ]]; then
    ARGS="$ARGS -dist"
    [[ -n "$DISTRIBUTED_IP" ]] && ARGS="$ARGS -dist_ip $DISTRIBUTED_IP"
    [[ -n "$DISTRIBUTED_USERNAME" ]] && ARGS="$ARGS -dist_username $DISTRIBUTED_USERNAME"
    [[ -n "$DISTRIBUTED_DIR" ]] && ARGS="$ARGS -dist_host_directory $DISTRIBUTED_DIR"
fi

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_PATH")"

# Execute Docker command
echo "Running PTZJEPA with arguments: $ARGS"
sudo docker run --privileged --rm --gpus all \
  -v "$PERSISTENCE_PATH":/persistence \
  -v "$APP_PATH":/app \
  "$DOCKER_IMAGE" \
  python3 /app/main.py $ARGS 2>&1 | tee "$LOG_PATH"