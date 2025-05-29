# World Model Data Transfer Sizes in PTZJEPA

Based on the repository structure and code implementation, the world model data transfers in the distributed setup involve these components:

## Model File Sizes

1. **Vision Transformer (ViT) Base Models**: 
   - Approximately 300-400MB per model checkpoint
   - These include both encoder and predictor networks from the JEPA architecture

2. **Reinforcement Learning Agent Models**:
   - About 20-50MB per agent model
   - Includes policy network and value function parameters

## Data Transfers During Operation

When running in distributed mode (`-dist` flag), the system transfers:

1. **Initial Mount**: Full model files are mounted via SSHFS from the remote server
   - This creates a baseline transfer of ~400-500MB when a node starts

2. **Incremental Updates**:
   - Model checkpoint files when training completes
   - These occur after each successful training iteration
   - Typically 300-400MB per update

3. **Redis Communications**:
   - Very small (few KB) for lock management
   - Just contains metadata about which models are in use

## Storage Requirements

The persistence folder structure shows model storage paths:
```
./world_models  # Contains the trained world models (several GB total)
./agents        # Contains the trained RL agents (hundreds of MB)
```

For a typical deployment with multiple models, expect 5-10GB of total storage for model files, with individual transfers in the hundreds of MB range during operation.