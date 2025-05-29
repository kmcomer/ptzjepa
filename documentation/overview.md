# PTZJEPA Repository Structure

The repository is organized around a project for Pan-Tilt-Zoom camera control using Joint Embedding Predictive Architecture (JEPA). Here's the structure breakdown:

## Root Directory
- main.py: Entry point script that orchestrates the entire workflow
- Dockerfile: Container definition for deployment
- README.md: Project documentation
- requirements.txt: Python dependencies

## Key Directories

### configs
- Contains configuration files like `Config_file.yaml` for system parameters

### figures
- Visualization assets including diagrams for the architecture (`Diagram.png`, `Federated.png`) and result visualizations

### notebooks
- Jupyter notebooks for analysis and visualization:
  - analyze_pointing.ipynb: Camera positioning analysis
  - gen_embed.ipynb: Embedding generation
  - parse_output.ipynb: Results parsing
  - test_infer.ipynb: Model inference testing

### source (Core codebase)
- **Camera Control**
  - Protocol implementations: `onvif_control.py`, `sunapi_control.py`, `vapix_control.py`
  - Configuration files: `onvif_config.py`, `sunapi_config.py`, `vapix_config.py`

- **Dataset Management**
  - prepare_dataset.py: Dataset preparation utilities
  - `/datasets`: Dataset classes for PTZ cameras and "dreams" (generated data)

- **Model Implementation**
  - `/models`: Contains Vision Transformer implementation
  - `helper.py`: Model utility functions
  - `transforms.py`: Data transformation pipelines

- **Training & Execution**
  - run_jepa.py: JEPA model training
  - run_rl.py: Reinforcement learning training
  - `rl_helper.py`: RL utilities
  - `env_interaction.py`: Environment interaction logic
  - track_progress.py: Training progress tracking

- **Utilities**
  - `/utils`: Supporting functions for logging, distributed training (redis), schedulers

- **Analysis**
  - analysis_viz.py: Analysis and visualization tools
  - gen_embed.py: Embedding generation tools

The structure follows a modular design that separates camera control, model training, data management, and analysis components, making the codebase organized and maintainable.