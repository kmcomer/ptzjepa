# Fixing "The Proxy Server is Refusing Connections" for Jupyter Access

This error typically occurs when the SSH tunnel isn't properly established or the Jupyter server isn't running correctly. Here's how to troubleshoot:

## Check if Jupyter is Running

First, verify the Jupyter container is running on the node:

```bash
sudo docker ps | grep jupyter
```

If it's not running, start it with:

```bash
sudo docker run --name ptzjepa-jupyter --rm --gpus all \
  -v /home/waggle/dario/JEPA_Persistence:/persistence \
  -v /home/waggle/dario/ptzjepa:/app \
  -p 8888:8888 \
  dariodematties/ptzjepa:latest \
  bash -c "pip install jupyter matplotlib scikit-learn && jupyter-lab --port 8888 --no-browser --allow-root --ip 0.0.0.0"
```

## Check Jupyter's Status

Look at the container logs to confirm Jupyter started properly:

```bash
sudo docker logs ptzjepa-jupyter
```

Look for a line like:
```
[I 2025-05-17 06:XX:XX ServerApp] Jupyter Server ... is running at:
[I 2025-05-17 06:XX:XX ServerApp] http://127.0.0.1:8888/lab?token=...
```

## Fix SSH Tunneling

The error suggests your SSH tunnel isn't working. Try these steps:

1. **Close any existing SSH connections** to the node

2. **Create a new SSH tunnel with verbose output**:
   ```bash
   ssh -v -L 8888:localhost:8888 waggle@sb-core-00002CEA7FA13644
   ```

3. **Try a different local port** in case 8888 is already in use:
   ```bash
   ssh -L 9999:localhost:8888 waggle@sb-core-00002CEA7FA13644
   ```
   Then access http://localhost:9999

## Alternative Direct Access

If the node has a public IP and allows direct connections:

```bash
# Check if the node accepts direct connections
sudo docker run --name ptzjepa-jupyter --rm --gpus all \
  -v /home/waggle/dario/JEPA_Persistence:/persistence \
  -v /home/waggle/dario/ptzjepa:/app \
  -p 0.0.0.0:8888:8888 \
  dariodematties/ptzjepa:latest \
  bash -c "pip install jupyter matplotlib scikit-learn && jupyter-lab --port 8888 --no-browser --allow-root --ip 0.0.0.0"
```

Then try accessing: `http://<node-ip>:8888`

## Check for Firewall Issues

If you still can't connect, check if a firewall is blocking the connection:

```bash
sudo iptables -L | grep 8888
```

This comprehensive approach should resolve the connection issue and give you access to your Jupyter environment.