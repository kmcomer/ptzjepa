# Pan Tilt Zoom Joint Embedding Predictive Architecture (PTZJEPA)

## Buiding the PTZJEPA

To build the PTZJEPA and push it to dockerhub, you need to have Docker installed in your local machine. Then, you can run the following command:

```bash
sudo docker buildx build --platform=linux/amd64 -t your_dockerhub_username/ptzjepa -f Dockerfile --push .
```

once the build is done and the image is pushed to your DockerHub, you can run the following command to pull the image in a dell blade server:

```bash
sudo docker image pull your_dockerhub_username/ptzjepa
```

## Running the PTZJEPA container on a Dell Blade Server

To run the PTZJEPA container on a Dell Blade Server, you can run the following command:

```bash
sudo docker run --gpus all --privileged -it -v /path/to/jepa/persistece/folder:/persistence -v /path/to/ptzjepa:/app your_dockerhub_username/ptzjepa:latest bash
```

The command above will run the container in bash mode.

To run the PTZJEPA in the container, you can run the following command:

```bash
sudo docker run --privileged --rm --gpus all -v /path/to/jepa/persistece/folder:/persistence -v /path/to/ptzjepa:/app your_dockerhub_username/ptzjepa:latest python /app/main.py -tp -cb 0 -it 20 -mv 20 -un camera_username -pw camera_password -ip xxx.xxx.xx.xx -rm lifelong --track_all -ki --debug 2>&1 | tee /path/to/log.out
```

where `/path/to/jepa/persistece/folder` is the path to the folder where the JEPA persistence files are stored and `/path/to/ptzjepa` is the path to the PTZJEPA folder.

The persistence folder should contain the following structure:

```
.
./collected_imgs
./collected_commands
./collected_positions
./collected_embeds
./world_models
./agents
./progress_model_names.txt
```

## Visualizing the PTZJEPA outputs

From the Dell Blade Server, you can run the following command to activate the juptyer notebook:

```bash
ROOTDIR=/path/to/ptzjepa/parent/folder
```

```bash
sudo docker run --name jupyter --rm --gpus all -v $ROOTDIR:/envroot -v $ROOTDIR/ptzjepa:/app -it -p 8888:8888 your_dockerhub_username/ptzjepa:latest bash -c "pip install jupyter matplotlib scikit-learn && jupyter-lab --port 8888 --no-browser --allow-root --ip 0.0.0.0"
```

Then, on another terminal window, you can run the following command:

```bash
ssh -L 8888:localhost:8888 waggle-dev-node-v010
```


### 1- Setting Up the Environment Variable

```bash
ROOTDIR=/path/to/ptzjepa/parent/folder
```

Purpose: This line assigns the path `/path/to/ptzjepa/parent/folder` to an environment variable named `ROOTDIR`.

Why? Later in the command, we use `$ROOTDIR` to refer to this directory. This helps avoid typing the full path multiple times and makes the command more flexible.


### 2- Running the Docker Container

```bash
sudo docker run --name jupyter --rm --gpus all -v $ROOTDIR:/envroot -v $ROOTDIR/ptzjepa:/app -it -p 8888:8888 your_dockerhub_username/ptzjepa:latest bash -c "pip install jupyter matplotlib scikit-learn && jupyter-lab --port 8888 --no-browser --allow-root --ip 0.0.0.0"
```

This is a long command. Let’s dissect it piece by piece:

a. Docker Command and Flags

`sudo docker run`:
Runs a new Docker container. sudo is used to run Docker with elevated privileges.

`--name jupyter`:
Names the container "jupyter". This makes it easier to refer to the container later.

`--rm`:
Automatically removes the container once it stops. This prevents leftover containers from taking up resources.

`--gpus all`:
Allocates all available GPUs to the container. This is useful if your Jupyter notebooks or computations require GPU acceleration.

b. Volume Mounting with `-v`
`-v $ROOTDIR:/envroot`:
Mounts the host directory specified by `$ROOTDIR` to the container’s `/envroot` directory. This makes the files in `$ROOTDIR` accessible from inside the container.

`-v $ROOTDIR/ptzjepa:/app`:
Mounts the subdirectory ptzjepa (inside `$ROOTDIR`) to `/app` inside the container. Often, this might be where your application or code resides.

c. Interactive and Port Flags

`-it`:
Runs the container in interactive mode with a pseudo-TTY (terminal). This is useful for commands that require user interaction or for debugging.

`-p 8888:8888`:
Maps port 8888 on the host to port 8888 in the container. This is crucial for accessing the Jupyter server running inside the container from the host machine.

d. Docker Image

`your_dockerhub_username/ptzjepa:latest`:
Specifies the Docker image to use. Replace `your_dockerhub_username` with your actual Docker Hub username. The tag latest indicates that you’re using the most recent version of the image.

e. The Command Inside the Container

The final part of the Docker command is:

```bash
bash -c "pip install jupyter matplotlib scikit-learn && jupyter-lab --port 8888 --no-browser --allow-root --ip 0.0.0.0"
```

`bash -c "..."`:
Tells the container to execute the command string within the quotes in a new bash shell.

`pip install jupyter matplotlib scikit-learn`:
Installs the necessary Python packages (Jupyter Lab, Matplotlib, and scikit-learn) inside the container. This ensures that the container has all the dependencies required for your work.

`&&`:
Ensures that the next command (`jupyter-lab ...`) runs only if the pip install command succeeds.

`jupyter-lab --port 8888 --no-browser --allow-root --ip 0.0.0.0`:
Starts Jupyter Lab with the following options:

`--port 8888`: Runs the server on port 8888.
`--no-browser`: Prevents Jupyter from trying to open a web browser inside the container.
`--allow-root`: Allows Jupyter Lab to run as the root user (common in Docker containers).
`--ip 0.0.0.0`: Binds the server to all network interfaces, making it accessible from outside the container.

### 3- Creating an SSH Tunnel

```bash
ssh -L 8888:localhost:8888 waggle-dev-node-v010
```

Purpose: This command sets up an SSH tunnel to securely forward network traffic.

Breaking it down:

`ssh`: Initiates an SSH connection.

`-L 8888:localhost:8888`:
This flag tells SSH to forward traffic:

Local port 8888 on your machine
To port 8888 on localhost of the remote machine.
In other words, any request to `localhost:8888` on your computer will be securely tunneled to `localhost:8888` on the remote host.

`waggle-dev-node-v010`:
This is the hostname (or IP address) of the remote machine (in this case, likely one of the Dell Blade Servers).

### How It All Works Together

#### Docker Container Starts Jupyter Lab:

On the remote server (Dell Blade Server), the Docker container is started.

The container installs the required Python packages and then launches Jupyter Lab on port 8888.

Because of the `-p 8888:8888` flag, port 8888 inside the container is mapped to port 8888 on the host machine (the Dell Blade Server).

#### SSH Tunnel Bridges Your Local Machine and the Remote Server:

You run the SSH command in a separate terminal window.

This command creates a secure tunnel from your local machine’s port 8888 to the remote server’s port 8888.

As a result, when you open a web browser on your local machine and navigate to `http://localhost:8888`, you’re actually accessing the Jupyter Lab instance running inside the Docker container on the remote server.
