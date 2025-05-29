# When to Build and Push the PTZJEPA Docker Image

You would need to build and push a new Docker image to Docker Hub in these situations:

## 1. Code Changes
When you make changes to the PTZJEPA codebase, including:
- Adding new features to any Python files
- Fixing bugs in the implementation
- Modifying the reinforcement learning algorithm
- Updating the world model architecture

## 2. Dependency Updates
- When adding new Python packages to requirements.txt
- When updating versions of existing dependencies
- When changing system-level dependencies in the Dockerfile

## 3. Configuration Changes
- If you modify the default configuration that should be baked into the image
- When adding new command-line parameters to main.py

## 4. Deployment to New Nodes
- When setting up the system on new nodes that don't have the image cached
- When you want all nodes to use the exact same environment

## 5. Version Management
- When releasing a stable version that should be tagged specifically
- When creating different variants of the system for different use cases

To build and push the Docker image:

```bash
# Navigate to the directory with the Dockerfile
cd /path/to/ptzjepa

# Build the Docker image
docker build -t your_dockerhub_username/ptzjepa:latest .

# Push to Docker Hub
docker push your_dockerhub_username/ptzjepa:latest

# Optionally tag with version
docker tag your_dockerhub_username/ptzjepa:latest your_dockerhub_username/ptzjepa:v1.0.0
docker push your_dockerhub_username/ptzjepa:v1.0.0
```