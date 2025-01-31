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
