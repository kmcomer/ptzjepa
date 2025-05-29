# Collecting Network Performance Data Between PTZJEPA Nodes

To collect data about network performance between nodes in your distributed PTZJEPA setup, you can implement monitoring at several levels. Here's a comprehensive approach:

## 1. Create a Network Monitoring Module

First, create a dedicated module for network metrics:

```python
import time
import subprocess
import socket
import requests
import logging
from functools import wraps
from collections import defaultdict
import csv
import os
from datetime import datetime

logger = logging.getLogger(__name__)
network_stats = defaultdict(list)

def measure_latency(host, count=5):
    """Measure latency to host using ping"""
    try:
        output = subprocess.check_output(
            ["ping", "-c", str(count), host],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Extract average round-trip time
        lines = output.split('\n')
        for line in lines:
            if 'avg' in line:
                # Example line: "round-trip min/avg/max/stddev = 0.046/0.057/0.065/0.007 ms"
                avg_latency = float(line.split('/')[1])
                return avg_latency
        return None
    except subprocess.CalledProcessError:
        logger.error(f"Failed to ping {host}")
        return None

def check_throughput(host, port=22, duration=5, size_mb=10):
    """Measure network throughput using iperf3"""
    try:
        # Check if iperf3 is installed
        subprocess.check_output(["which", "iperf3"])
        
        # Run iperf3 client
        output = subprocess.check_output(
            ["iperf3", "-c", host, "-p", str(port), "-t", str(duration), "-n", f"{size_mb}M"],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Parse output for bandwidth
        for line in output.split('\n'):
            if 'sender' in line and 'Mbits/sec' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'Mbits/sec':
                        bandwidth = float(parts[i-1])
                        return bandwidth
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("iperf3 test failed - ensure iperf3 is installed and server is running on target")
        return None

def log_network_metrics(host, port=22):
    """Log comprehensive network metrics to a single record"""
    metrics = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'host': host,
        'latency_ms': None,
        'packet_loss_pct': None,
        'throughput_mbps': None
    }
    
    # Measure latency and packet loss with ping
    try:
        ping_output = subprocess.check_output(
            ["ping", "-c", "10", host],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Extract statistics
        for line in ping_output.split('\n'):
            if 'min/avg/max' in line:
                parts = line.split('=')[1].strip().split('/')
                metrics['latency_ms'] = float(parts[1])
            if 'packet loss' in line:
                metrics['packet_loss_pct'] = float(line.split('%')[0].split()[-1])
    except:
        logger.error(f"Failed to collect ping metrics for {host}")
    
    # Measure throughput if possible
    metrics['throughput_mbps'] = check_throughput(host, port)
    
    # Log metrics
    network_stats[host].append(metrics)
    logger.info(f"NETWORK: {host} | Latency: {metrics['latency_ms']}ms | "
                f"Loss: {metrics['packet_loss_pct']}% | "
                f"Throughput: {metrics['throughput_mbps']} Mbps")
    
    return metrics

def save_network_stats_to_csv(filename="/persistence/network_metrics.csv"):
    """Save network metrics to CSV file"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Check if file exists
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'host', 'latency_ms', 'packet_loss_pct', 'throughput_mbps']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for host, metrics_list in network_stats.items():
            for metrics in metrics_list:
                writer.writerow(metrics)
```

## 2. Modify Distributed Code to Track Network Performance

Update the SSHFS mounting class to include network monitoring:

```python
from source.utils.network_monitor import log_network_metrics, save_network_stats_to_csv

class SSHFSMounter:
    def __init__(self, host_username, host_ip, host_data_directory, local_data_directory, identity_file):
        # Existing initialization code...
        self.host_ip = host_ip
        self.host_username = host_username
        # Rest of existing code...

    def mount(self):
        # Log network metrics before mounting
        metrics = log_network_metrics(self.host_ip)
        
        # Existing mount code...
        success = subprocess.call(mount_command, shell=True) == 0
        
        # Log metrics again after mount
        if success:
            log_network_metrics(self.host_ip)
            
        return success

    def unmount(self):
        # Existing unmount code...
        pass
```

## 3. Add Network Monitoring to Redis Operations

Extend the `MultiLockerSystem` class to track network performance:

```python
from source.utils.network_monitor import log_network_metrics

class MultiLockerSystem:
    def __init__(self, redis_host, redis_port, redis_password, locker_prefix, num_lockers, expire_in_sec=1800, acquire_timeout=10):
        # Existing initialization...
        self.redis_host = redis_host
        
        # Add network monitoring
        self.network_stats = []
        # Initial network measurement
        self.measure_network()

    def measure_network(self):
        """Measure network performance to Redis server"""
        metrics = log_network_metrics(self.redis_host, self.redis.connection_pool.connection_kwargs.get('port', 6379))
        self.network_stats.append(metrics)
        return metrics

    def acquire_locker(self, locker_num):
        # Measure network before operation
        start_time = time.time()
        result = None
        
        # Existing code...
        locker_name = f"{self.locker_prefix}:{locker_num}"
        end_time = time.time() + self.acquire_timeout
        while time.time() < end_time:
            if self.redis.set(locker_name, self.identifier, nx=True, ex=self.expire_in_sec):
                result = locker_num
                break
            time.sleep(0.1)
        
        # Measure operation latency and log
        op_time = time.time() - start_time
        logger.info(f"REDIS: acquire_locker took {op_time*1000:.2f}ms")
        
        # Periodically measure network (e.g., every 10 operations)
        if random.random() < 0.1:  # ~10% of operations
            self.measure_network()
            
        return result
```

## 4. Integrate with Main Lifelong Learning Loop

Add periodic network monitoring to the main lifelong learning function:

```python
from source.utils.network_monitor import log_network_metrics, save_network_stats_to_csv

@timeit("lifelong_learning_cycle")
def lifelong_learning(arguments):
    operate_ptz(arguments)
    cycle_count = 0
    
    # Initialize network monitoring if distributed mode is enabled
    if arguments.distributed:
        network_hosts = [arguments.distributed_ip]  # Add other nodes as needed
    
    while True:
        cycle_count += 1
        logger.info(f"Starting lifelong learning cycle {cycle_count}")
        
        # Periodic network performance check
        if arguments.distributed and cycle_count % 5 == 0:  # Every 5 cycles
            for host in network_hosts:
                log_network_metrics(host)
        
        # Existing lifecycle code...
        
        # Save network stats to CSV at the end of each cycle
        if arguments.distributed:
            save_network_stats_to_csv()
```

## 5. Add a Dedicated Network Testing Tool

Create a standalone script for more comprehensive network testing:

```python
#!/usr/bin/env python3
import argparse
import time
import subprocess
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def run_network_tests(target, duration=60, interval=5):
    """Run extended network tests and visualize results"""
    timestamps = []
    latencies = []
    packet_losses = []
    
    start_time = time.time()
    end_time = start_time + duration
    
    print(f"Running network tests to {target} for {duration} seconds...")
    
    while time.time() < end_time:
        current_time = datetime.now().strftime("%H:%M:%S")
        timestamps.append(current_time)
        
        # Run ping test
        try:
            output = subprocess.check_output(
                ["ping", "-c", "5", target],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Extract latency
            latency = None
            packet_loss = None
            
            for line in output.split('\n'):
                if 'min/avg/max' in line:
                    parts = line.split('=')[1].strip().split('/')
                    latency = float(parts[1])  # avg latency
                if 'packet loss' in line:
                    packet_loss = float(line.split('%')[0].split()[-1])
            
            latencies.append(latency if latency is not None else float('nan'))
            packet_losses.append(packet_loss if packet_loss is not None else float('nan'))
            
            print(f"[{current_time}] Latency: {latency}ms, Packet Loss: {packet_loss}%")
        except:
            print(f"[{current_time}] Test failed")
            latencies.append(float('nan'))
            packet_losses.append(float('nan'))
        
        # Sleep until next interval
        time.sleep(interval)
    
    # Create visualizations
    plt.figure(figsize=(10, 6))
    plt.subplot(2, 1, 1)
    plt.plot(timestamps, latencies, 'b-o')
    plt.title(f"Network Latency to {target}")
    plt.ylabel("Latency (ms)")
    plt.xticks(rotation=45)
    
    plt.subplot(2, 1, 2)
    plt.plot(timestamps, packet_losses, 'r-o')
    plt.title(f"Packet Loss to {target}")
    plt.ylabel("Loss (%)")
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f"/persistence/network_test_{target.replace('.', '_')}_{int(time.time())}.png")
    
    # Save raw data
    results = {
        "target": target,
        "test_duration": duration,
        "interval": interval,
        "timestamps": timestamps,
        "latencies": latencies,
        "packet_losses": packet_losses
    }
    
    with open(f"/persistence/network_test_{target.replace('.', '_')}_{int(time.time())}.json", 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network Performance Testing Tool")
    parser.add_argument("target", help="Target host to test")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Test interval in seconds")
    
    args = parser.parse_args()
    run_network_tests(args.target, args.duration, args.interval)
```

## 6. Add Network Monitoring to get_argparser in main.py

Update the argument parser to include network monitoring options:

```python
def get_argparser():
    parser = argparse.ArgumentParser("PTZ JEPA")
    # Existing arguments...
    
    # Network monitoring options
    parser.add_argument(
        "-nm",
        "--network_monitoring",
        action="store_true",
        help="Enable detailed network performance monitoring"
    )
    parser.add_argument(
        "-ni",
        "--network_interval",
        type=int,
        default=300,  # 5 minutes
        help="Interval in seconds between network measurements"
    )
    parser.add_argument(
        "-nh",
        "--network_hosts",
        type=str,
        default="",
        help="Comma-separated list of additional hosts to monitor network performance to"
    )
    
    return parser
```

These implementations will allow you to collect comprehensive network performance data between your PTZJEPA nodes, providing insights into latency, throughput, and packet loss that can help diagnose performance issues and optimize your distributed system.