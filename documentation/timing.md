# Measuring PTZJEPA Stage Durations

To measure the duration of the different processing stages in the PTZJEPA system, you'll need to modify code in several files. Here's a comprehensive approach:

## 1. Add Timing Utilities in utils

First, create a timing utility:

```python
import time
import logging
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)
timing_stats = defaultdict(list)

def timeit(stage_name):
    """Decorator to measure execution time of functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            timing_stats[stage_name].append(elapsed)
            logger.info(f"TIMING: {stage_name} took {elapsed:.2f} seconds")
            return result
        return wrapper
    return decorator

def print_timing_summary():
    """Print summary of all timings collected"""
    logger.info("===== TIMING SUMMARY =====")
    for stage, times in timing_stats.items():
        avg_time = sum(times) / len(times) if times else 0
        total_time = sum(times)
        count = len(times)
        logger.info(f"Stage: {stage} | Count: {count} | Avg: {avg_time:.2f}s | Total: {total_time:.2f}s")
    logger.info("=========================")
```

## 2. Modify Main Wrapper Functions in main.py

```python
from source.utils.timing import timeit, print_timing_summary

# Modify each wrapper function with timing decorator
@timeit("pretraining")
def pretraining_wrapper(arguments):
    # ...existing code...

@timeit("world_model_training")
def pretraining_world_model_wrapper(arguments):
    # ...existing code...

@timeit("dreaming")
def dreamer_wrapper(arguments):
    # ...existing code...

@timeit("rl_training")
def behavior_learning(arguments):
    # ...existing code...

@timeit("environment_interaction")
def environment_interaction(arguments):
    # ...existing code...

# Add timing summary at the end of main()
def main():
    # ...existing code...
    
    # Add before the final logger.info("DONE!")
    print_timing_summary()
    
    logger.info("DONE!")
```

## 3. Add Sub-Stage Timing in Module Functions

### In `run_jepa.py`:
```python
from source.utils.timing import timeit

@timeit("jepa_epoch")
def train_one_epoch(model, data_loader, optimizer, ...):
    # ...existing code...

@timeit("dream_generation")
def generate_dreams(...):
    # ...existing code...
```

### In `run_rl.py`:
```python
from source.utils.timing import timeit

@timeit("rl_train_episode")
def train_episode(...):
    # ...existing code...

@timeit("optimize_model")
def optimize_model(...):
    # ...existing code...
```

### In `env_interaction.py`:
```python
from source.utils.timing import timeit

@timeit("camera_movement")
def set_relative_position(...):
    # ...existing code...

@timeit("env_step")
def step(...):
    # ...existing code...
```

## 4. Add Detailed Performance Logging to `lifelong_learning`

```python
@timeit("lifelong_learning_cycle")
def lifelong_learning(arguments):
    operate_ptz(arguments)
    cycle_count = 0
    
    while True:
        cycle_count += 1
        logger.info(f"Starting lifelong learning cycle {cycle_count}")
        
        start_time = time.time()
        prepare_images()
        img_time = time.time() - start_time
        
        start_time = time.time()
        training_complete = run_jepa(arguments.fname, "world_model")
        world_model_time = time.time() - start_time
        
        start_time = time.time()
        training_complete = run_jepa(arguments.fname, "dreamer")
        dreamer_time = time.time() - start_time
        
        start_time = time.time()
        training_complete = run_rl(arguments.fname, "train_agent")
        rl_time = time.time() - start_time
        
        start_time = time.time()
        interaction_complete = env_inter(arguments, arguments.fname, "navigate_env")
        interaction_time = time.time() - start_time
        
        logger.info(f"Cycle {cycle_count} timing - "
                   f"Image prep: {img_time:.2f}s, "
                   f"World model: {world_model_time:.2f}s, " 
                   f"Dreaming: {dreamer_time:.2f}s, "
                   f"RL: {rl_time:.2f}s, "
                   f"Interaction: {interaction_time:.2f}s")
```

## 5. Add CSV Logging for Analysis

```python
# Add to the existing timing.py file

import csv
import os
from datetime import datetime

def save_timings_to_csv(filename="/persistence/timing_logs.csv"):
    """Save all timing data to CSV file"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'stage', 'duration']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for stage, times in timing_stats.items():
            for duration in times:
                writer.writerow({
                    'timestamp': timestamp,
                    'stage': stage,
                    'duration': f"{duration:.4f}"
                })

# Add this call to the print_timing_summary function
def print_timing_summary():
    # ...existing code...
    save_timings_to_csv()
```

These modifications will give you detailed timing information for each stage of the PTZJEPA system, both in logs and as structured CSV data that you can analyze later.