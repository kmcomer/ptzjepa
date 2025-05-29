# PTZJEPA Node Commands

## Basic Docker Operations
```bash
# Pull the PTZJEPA image
sudo docker image pull your_dockerhub_username/ptzjepa

# Run interactive container with bash shell
sudo docker run --gpus all --privileged -it \
  -v /path/to/persistence:/persistence \
  -v /path/to/ptzjepa:/app \
  your_dockerhub_username/ptzjepa:latest bash
```

## Running PTZJEPA in Different Modes
```bash
# Run in lifelong learning mode (standard operation)
sudo docker run --privileged --rm --gpus all \
  -v /path/to/persistence:/persistence \
  -v /path/to/ptzjepa:/app \
  your_dockerhub_username/ptzjepa:latest \
  python /app/main.py -rm lifelong -tp -cb 0 \
  -un camera_username -pw camera_password -ip xxx.xxx.xx.xx \
  -it 20 -mv 20 --track_all -ki --debug 2>&1 | tee /path/to/log.out

# Run in federated learning mode (distributed)
sudo docker run --privileged --rm --gpus all \
  -v /path/to/persistence:/persistence \
  -v /path/to/ptzjepa:/app \
  your_dockerhub_username/ptzjepa:latest \
  python /app/main.py -rm lifelong -dist \
  -un camera_username -pw camera_password -ip xxx.xxx.xx.xx \
  -it 20 -mv 20 --track_all -ki --debug 2>&1 | tee /path/to/log.out
```

## Alternative Operation Modes
Replace `-rm lifelong` with any of these modes:
```
-rm train              # Run basic pretraining
-rm world_model_train  # Train only the world model
-rm dream              # Generate dreams from trained world model
-rm agent_train        # Train only the RL agent
-rm env_interaction    # Run only environment interaction
```

## Visualization Setup
```bash
# Set environment variable for your data directory
ROOTDIR=/path/to/ptzjepa/parent/folder

# Run Jupyter Lab for visualization
sudo docker run --name jupyter --rm --gpus all \
  -v $ROOTDIR:/envroot \
  -v $ROOTDIR/ptzjepa:/app \
  -it -p 8888:8888 \
  your_dockerhub_username/ptzjepa:latest \
  bash -c "pip install jupyter matplotlib scikit-learn && jupyter-lab --port 8888 --no-browser --allow-root --ip 0.0.0.0"

# Create SSH tunnel to access Jupyter (run from your local machine)
ssh -L 8888:localhost:8888 waggle-dev-node-v010
```

## Distributed Setup Commands
```bash
# Copy SSH key to Redis server (for distributed mode)
ssh-copy-id -i /root/.ssh/id_rsa.pub waggle@xxx.xxx.xx.xx

# Manually mount remote filesystem if needed
sshfs -o IdentityFile=/root/.ssh/id_rsa -o StrictHostKeyChecking=no \
  waggle@130.202.23.67:/path/to/world_models \
  /persistence/world_models/
```