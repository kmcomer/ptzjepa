import os
import redis
import signal
import time
import uuid
import sys
import subprocess
from pathlib import Path

class MultiLockerSystem:
    def __init__(self, redis_host, redis_port, redis_password, locker_prefix, num_lockers, expire_in_sec=1800, acquire_timeout=10):
        self.redis = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)
        self.locker_prefix = locker_prefix
        self.num_lockers = num_lockers
        self.expire_in_sec = expire_in_sec
        self.acquire_timeout = acquire_timeout
        self.identifier = str(uuid.uuid4())

    def acquire_locker(self, locker_num):
        locker_name = f"{self.locker_prefix}:{locker_num}"
        end_time = time.time() + self.acquire_timeout
        while time.time() < end_time:
            if self.redis.set(locker_name, self.identifier, nx=True, ex=self.expire_in_sec):
                return locker_num
            time.sleep(0.1)
        return None  # Acquisition timeout

    def release_locker(self, locker_num):
        locker_name = f"{self.locker_prefix}:{locker_num}"
        pipe = self.redis.pipeline(True)
        while True:
            try:
                pipe.watch(locker_name)
                value = pipe.get(locker_name)
                if value and value.decode('utf-8') == self.identifier:
                    pipe.multi()
                    pipe.delete(locker_name)
                    pipe.execute()
                    return True
                pipe.unwatch()
                break
            except redis.WatchError:
                continue  # Retry on watch error
            except Exception as e:
                pipe.reset()
                print(f"Error releasing lock: {e}")
                break
        return False

# class MultiLockerSystem:
#     def __init__(self, redis_host, redis_port, redis_password, locker_prefix, num_lockers, expire_in_sec=1800):
#         self.redis = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)
#         self.locker_prefix = locker_prefix
#         self.num_lockers = num_lockers
#         self.expire_in_sec = expire_in_sec
#         self.identifier = str(uuid.uuid4())
#
#     def acquire_locker(self, locker_num):
#         end = time.time() + self.expire_in_sec
#         while time.time() < end:
#             #for i in range(self.num_lockers):
#                 #locker_name = f"{self.locker_prefix}:{i}"
#             locker_name = f"{self.locker_prefix}:{locker_num}"
#             if self.redis.setnx(locker_name, self.identifier):
#                 self.redis.expire(locker_name, self.expire_in_sec)
#                 return locker_num  # Return the locker number
#                 #return i  # Return the locker number
#             time.sleep(0.1)
#         return None  # Couldn't acquire any locker within the time limit
#
#     def release_locker(self, locker_num):
#         locker_name = f"{self.locker_prefix}:{locker_num}"
#         pipe = self.redis.pipeline(True)
#         while True:
#             try:
#                 pipe.watch(locker_name)
#                 if pipe.get(locker_name).decode('utf-8') == self.identifier:
#                     pipe.multi()
#                     pipe.delete(locker_name)
#                     pipe.execute()
#                     return True
#                 pipe.unwatch()
#                 break
#             except redis.WatchError:
#                 pass
#         return False
#



class SSHFSMounter:
    def __init__(self, host_username, host_ip, host_data_directory, local_data_directory, identity_file="/root/.ssh/id_rsa"):
        self.host_username = host_username
        self.host_ip = host_ip
        self.host_data_directory = host_data_directory
        self.local_data_directory = local_data_directory
        self.identity_file = identity_file
        self.mount_proc = None  # Will store the sshfs process

    def run_command(self, command, timeout=30):
        print(f"Executing command: {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"Command timed out after {timeout} seconds")
            return False

    def check_ssh(self):
        print("Checking SSH connection...")
        command = [
            'ssh', '-i', self.identity_file,
            '-o', 'StrictHostKeyChecking=no',
            f'{self.host_username}@{self.host_ip}', 'echo', 'SSH connection successful'
        ]
        return self.run_command(command)

    def check_sftp(self):
        print("Checking SFTP connection...")
        command = [
            'sftp',
            '-o', f'IdentityFile={self.identity_file}',
            '-o', 'StrictHostKeyChecking=no',
            f'{self.host_username}@{self.host_ip}:/'
        ]
        return self.run_command(command, timeout=10)

    def check_fuse(self):
        print("Checking FUSE availability...")
        return self.run_command(['fusermount', '-V'])

    def check_sshfs(self):
        print("Checking sshfs availability...")
        return self.run_command(['sshfs', '-V'])

    def mount(self):
        print("Starting mount process...")

        if not self.check_ssh():
            print("SSH connection failed. Cannot proceed with mount.")
            return False

        if not self.check_sftp():
            print("SFTP connection failed. Cannot proceed with mount.")
            return False

        if not self.check_fuse():
            print("FUSE is not available. Cannot proceed with mount.")
            return False

        if not self.check_sshfs():
            print("sshfs is not available. Cannot proceed with mount.")
            return False

        Path(self.local_data_directory).mkdir(parents=True, exist_ok=True)
        os.chmod(self.local_data_directory, 0o777)

        mount_command = [
            'sshfs',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', f'IdentityFile={self.identity_file}',
            f'{self.host_username}@{self.host_ip}:{self.host_data_directory}',
            self.local_data_directory
        ]

        print("Executing sshfs mount command in background...")
        # Launch sshfs in the background
        proc = subprocess.Popen(mount_command)
        # Wait a few seconds for the mount to be established
        time.sleep(5)
        if self.verify_mount():
            print("Mount verified successfully.")
            self.mount_proc = proc  # Save the process handle for later unmounting
            return True
        else:
            print("Mount verification failed, terminating sshfs process.")
            proc.terminate()
            return False

    def verify_mount(self):
        try:
            subprocess.run(['mountpoint', '-q', self.local_data_directory], check=True, timeout=5)
            print("Mount verified successfully.")
            return True
        except subprocess.CalledProcessError:
            print("Mount verification failed. The directory is not mounted.")
        except subprocess.TimeoutExpired:
            print("Mount verification timed out")
        return False

    def unmount(self):
        print("Starting unmount process...")
        unmount_command = ['fusermount', '-u', self.local_data_directory]
        # unmount_command = ['fusermount', '-u', '-v', self.local_data_directory]
        if self.run_command(unmount_command):
            print("Unmount successful")
            # Optionally, terminate the sshfs process if it’s still running
            if self.mount_proc is not None:
                self.mount_proc.terminate()
                self.mount_proc = None
        else:
            print("Unmount failed")
