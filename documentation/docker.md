# Dockerizing PTZJEPA with Docker Compose

To fully dockerize the PTZJEPA application for simplified deployment, you'll need to create a Docker Compose setup that encapsulates all configuration options.

## 1. Create `docker-compose.yml`

```yaml
version: '3'

services:
  ptzjepa:
    build:
      context: .
      dockerfile: Dockerfile
    image: ptzjepa:latest
    container_name: ptzjepa
    restart: unless-stopped
    privileged: true
    environment:
      - CAMERA_IP=${CAMERA_IP:-192.168.1.100}
      - CAMERA_USERNAME=${CAMERA_USERNAME:-admin}
      - CAMERA_PASSWORD=${CAMERA_PASSWORD:-password}
      - CAMERA_BRAND=${CAMERA_BRAND:-0}
      - RUN_MODE=${RUN_MODE:-lifelong}
      - ITERATIONS=${ITERATIONS:-20}
      - MOVEMENTS=${MOVEMENTS:-20}
      - DEBUG=${DEBUG:-false}
      - TRACK_POSITIONS=${TRACK_POSITIONS:-true}
      - KEEP_IMAGES=${KEEP_IMAGES:-true}
      - TRACK_ALL=${TRACK_ALL:-true}
      - DISTRIBUTED=${DISTRIBUTED:-false}
      - DISTRIBUTED_IP=${DISTRIBUTED_IP:-130.202.23.67}
      - DISTRIBUTED_USERNAME=${DISTRIBUTED_USERNAME:-waggle}
      - DISTRIBUTED_DIR=${DISTRIBUTED_DIR:-/home/waggle/world_models}
    volumes:
      - ./persistence:/persistence
      - .:/app
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    logging:
      driver: "json-file"
      options:
        max-size: "200m"
        max-file: "10"

  jupyter:
    build:
      context: .
      dockerfile: Dockerfile
    image: ptzjepa:latest
    container_name: ptzjepa-jupyter
    command: >
      bash -c "pip install jupyter matplotlib scikit-learn &&
              jupyter-lab --port 8888 --no-browser --allow-root --ip 0.0.0.0"
    ports:
      - "8888:8888"
    volumes:
      - ./persistence:/persistence
      - .:/app
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

## 2. Modify Dockerfile to Incorporate Arguments

```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    sshfs \
    openssh-client \
    curl \
    iperf3 \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set up SSH for distributed mode
RUN mkdir -p /root/.ssh && \
    ssh-keygen -t rsa -f /root/.ssh/id_rsa -q -N ""

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create persistence directories
RUN mkdir -p /persistence/collected_imgs \
    /persistence/collected_commands \
    /persistence/collected_positions \
    /persistence/collected_embeds \
    /persistence/world_models \
    /persistence/agents

# Set the entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Default command to execute
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
```

## 3. Create Entry Point Script

```bash
#!/bin/bash
set -e

# Build command arguments
ARGS=""

# Camera settings
[[ -n "$CAMERA_IP" ]] && ARGS="$ARGS -ip $CAMERA_IP"
[[ -n "$CAMERA_USERNAME" ]] && ARGS="$ARGS -un $CAMERA_USERNAME"
[[ -n "$CAMERA_PASSWORD" ]] && ARGS="$ARGS -pw $CAMERA_PASSWORD"
[[ -n "$CAMERA_BRAND" ]] && ARGS="$ARGS -cb $CAMERA_BRAND"

# Run mode
[[ -n "$RUN_MODE" ]] && ARGS="$ARGS -rm $RUN_MODE"

# Operational parameters
[[ -n "$ITERATIONS" ]] && ARGS="$ARGS -it $ITERATIONS"
[[ -n "$MOVEMENTS" ]] && ARGS="$ARGS -mv $MOVEMENTS"

# Flags
[[ "$DEBUG" == "true" ]] && ARGS="$ARGS --debug"
[[ "$TRACK_POSITIONS" == "true" ]] && ARGS="$ARGS -tp"
[[ "$KEEP_IMAGES" == "true" ]] && ARGS="$ARGS -ki"
[[ "$TRACK_ALL" == "true" ]] && ARGS="$ARGS --track_all"

# Distributed mode settings
if [[ "$DISTRIBUTED" == "true" ]]; then
    ARGS="$ARGS -dist"
    [[ -n "$DISTRIBUTED_IP" ]] && ARGS="$ARGS -dist_ip $DISTRIBUTED_IP"
    [[ -n "$DISTRIBUTED_USERNAME" ]] && ARGS="$ARGS -dist_username $DISTRIBUTED_USERNAME"
    [[ -n "$DISTRIBUTED_DIR" ]] && ARGS="$ARGS -dist_host_directory $DISTRIBUTED_DIR"
fi

# If no command was provided, run the default application
if [ "$#" -eq 0 ]; then
    echo "Running with arguments: $ARGS"
    exec python /app/main.py $ARGS
else
    # Otherwise, run the provided command
    exec "$@"
fi
```

## 4. Create Environment Variables File

```bash
# Camera settings
CAMERA_IP=xxx.xxx.xx.xx
CAMERA_USERNAME=camera_username
CAMERA_PASSWORD=camera_password
CAMERA_BRAND=0

# Run settings
RUN_MODE=lifelong
ITERATIONS=20
MOVEMENTS=20
DEBUG=true
TRACK_POSITIONS=true
KEEP_IMAGES=true
TRACK_ALL=true

# Distributed settings
DISTRIBUTED=false
DISTRIBUTED_IP=130.202.23.67
DISTRIBUTED_USERNAME=waggle
DISTRIBUTED_DIR=/home/waggle/world_models
```

## 5. Usage Instructions

1. **Set up your environment variables**:
   - Edit the `.env` file with your specific settings

2. **Build and start the containers**:
   ```bash
   docker compose build
   docker compose up -d
   ```

3. **View logs**:
   ```bash
   docker compose logs -f ptzjepa
   ```

4. **Access Jupyter**:
   Open http://localhost:8888 in your browser
   (Token will be available in the jupyter container logs)

5. **Stop the containers**:
   ```bash
   docker compose down
   ```

This setup encapsulates all configuration in the Docker environment, making deployment consistent and simplified. You can still modify settings through the `.env` file without rebuilding the containers.