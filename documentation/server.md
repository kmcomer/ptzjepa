# PTZJEPA Server Architecture

## Server Role and Configuration

The PTZJEPA distributed system uses a **dedicated central server** (not one of the camera nodes) that serves two primary functions:

1. **Redis Server**: Manages distributed locks for coordinating access to shared resources
2. **File Server**: Provides shared storage for models via SSH File System (SSHFS)

The default server configuration in the code points to:
```
IP: 130.202.23.67
Username: waggle
Directory: /home/waggle/world_models
```

## Accessing the Server

Access the server using standard SSH:

```bash
ssh waggle@130.202.23.67
```

Authentication requires:
- SSH key authentication (preferred)
- Password authentication (if enabled)

Ensure your node's public key (`/root/.ssh/id_rsa.pub`) is added to the server:
```bash
ssh-copy-id -i /root/.ssh/id_rsa.pub waggle@130.202.23.67
```

## Server Setup Instructions

1. **Install Redis**:
   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

2. **Configure Redis**:
   ```bash
   sudo nano /etc/redis/redis.conf
   ```
   Modify:
   - `bind 0.0.0.0` (allow external connections)
   - `requirepass your_secure_password`
   - `protected-mode yes`

3. **Start/Restart Redis**:
   ```bash
   sudo systemctl restart redis-server
   sudo systemctl enable redis-server
   ```

4. **Create Shared Directory**:
   ```bash
   sudo mkdir -p /home/waggle/world_models
   sudo chown waggle:waggle /home/waggle/world_models
   chmod 755 /home/waggle/world_models
   ```

## Modifying Server Configuration

1. **Redis Configuration**:
   - Edit `/etc/redis/redis.conf` and restart the service
   - Key settings: memory limits, persistence options, network parameters

2. **SSH/SSHFS Configuration**:
   - Edit sshd_config for SSH server settings
   - Adjust permissions on shared directories

3. **Firewall Configuration**:
   ```bash
   sudo ufw allow 22/tcp      # SSH
   sudo ufw allow 6379/tcp    # Redis
   ```

4. **Update Client Configuration**:
   If server details change, update in PTZJEPA by modifying the command:
   ```bash
   python main.py -rm lifelong -dist -dist_ip new_ip -dist_username new_user -dist_host_directory new_path
   ```

The server can be hosted on any Linux system with sufficient storage and network capacity to handle model transfers between nodes.