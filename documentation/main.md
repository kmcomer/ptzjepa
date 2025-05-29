# Main.py Script Overview

main.py serves as the central orchestration script for a PTZ camera-based AI system that combines computer vision, reinforcement learning, and environmental interaction. Here's what it does:

## 1. Core Components
- **PTZ Camera Control**: Interfaces with pan-tilt-zoom cameras (supports Hanwha and Axis brands)
- **JEPA Training**: Manages Joint Embedding Predictive Architecture in different modes
- **Reinforcement Learning**: Handles agent training and behavior learning
- **Environment Interaction**: Manages the system's interaction with its environment

## 2. Operation Modes
The script offers six distinct operation modes selected via the `--run_mode` argument:
- **`train`**: Basic model pretraining using gathered images
- **`world_model_train`**: Specialized training for world models
- **`dream`**: Runs the "dreamer" mode which simulates scenarios
- **`agent_train`**: Focuses on training reinforcement learning agents
- **`env_interaction`**: Handles navigation and interaction with the environment
- **`lifelong`**: Continuous learning loop combining world modeling, dreaming, agent training, and environmental interaction

## 3. Execution Flow
1. Parses command-line arguments via `get_argparser()`
2. Configures logging based on debug settings
3. Sets up distributed computing if enabled (using SSH filesystem mounting)
4. Executes the appropriate wrapper function based on the selected mode
5. Handles cleanup operations when complete

## 4. Additional Features
- Distributed training support via SSH file system mounting
- Debug mode for verbose logging
- Configurable camera settings (IP, credentials, brand)
- Message publishing capability via "waggle plugin"

This script acts as the system's control center, coordinating data collection, model training, and environmental interaction in a modular, configurable framework.