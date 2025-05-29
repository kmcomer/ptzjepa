# How PTZJEPA Code Runs on a Node

The PTZJEPA code runs on a node through a Docker container-based workflow following these key steps:

## 1. Deployment Process
The code is deployed to a node (like a Waggle edge device) using Docker:

```bash
sudo docker run --privileged --rm --gpus all \
  -v /path/to/persistence:/persistence \
  -v /path/to/ptzjepa:/app \
  your_dockerhub_username/ptzjepa:latest \
  python /app/main.py -rm lifelong [other arguments]
```

## 2. Execution Flow in main.py
When started, main.py performs these operations:
- Parses command-line arguments via `get_argparser()`
- Configures logging based on the `--debug` flag
- Sets up GPU environment (`CUDA_VISIBLE_DEVICES`)
- Sets up distributed learning if the `--distributed` flag is used:
  - Mounts remote file system using `SSHFSMounter`
- Determines which mode to run based on the `--run_mode` parameter
- Executes the corresponding wrapper function
- Cleans up (unmounts shared filesystems, etc.) when complete

## 3. Operation Modes
Depending on the selected mode, different workflows are executed:

### Lifelong Learning Mode
The most comprehensive mode (`-rm lifelong`) runs a continuous loop:
```python
def lifelong_learning(arguments):
    operate_ptz(arguments)  # Initialize camera connection
    while True:
        prepare_images()  # Grab and process camera images
        run_jepa(arguments.fname, "world_model")  # Train world model
        run_jepa(arguments.fname, "dreamer")  # Generate dreams
        run_rl(arguments.fname, "train_agent")  # Train RL agent
        env_inter(arguments, arguments.fname, "navigate_env")  # Interact with camera
```

## 4. Data Management
The node stores and manages data in `/persistence` folder with this structure:
- `/collected_imgs`: Camera images
- `/collected_commands`: Camera movement commands
- `/collected_positions`: Camera position records
- `/collected_embeds`: Embedding vectors
- `/world_models`: Trained world models
- `/agents`: Trained agents

## 5. Distributed Learning
When running with `-dist` flag:
- The node mounts a remote filesystem using SSHFS
- Redis is used to coordinate access to shared models
- When a node needs to train a model or generate dreams:
  1. It locks the model via Redis (`acquire_locker()`)
  2. Processes the model
  3. Releases the lock (`release_locker()`)
  4. If a model is locked, nodes automatically try other available models

This approach enables federated learning across multiple camera locations.