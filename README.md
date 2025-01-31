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

where `/path/to/jepa/persistece/folder` is the path to the folder where the JEPA persistence files are stored and `/path/to/ptzjepa` is the path to the PTZJEPA folder.
