# Error Fix: KeyError 'restart_-1' in env_interaction.py

This error occurs in the `control_ptz` function when the `num_restart` value in `info_dict` is -1, causing the code to try accessing a non-existent key.

## Diagnosis

In `env_interaction.py`, the code is trying to access:
```python
restart_info = info_dict[f"restart_{info_dict['num_restart']:0>2}"]
```

The issue is that `info_dict['num_restart']` is `-1`, leading to a key of `restart_-1` which doesn't exist.

## Solution

Apply this patch to fix the issue:

```python
def control_ptz(env, camera_info, trajectories_folder, info_dict, args):
    # ...existing code...
    
    # REPLACE THIS LINE:
    # restart_info = info_dict[f"restart_{info_dict['num_restart']:0>2}"]
    
    # WITH THIS CODE:
    if info_dict['num_restart'] < 0:
        # Initialize restart counter if it's negative
        info_dict['num_restart'] = 0
        info_dict[f"restart_{info_dict['num_restart']:0>2}"] = {
            "start_ind": 0,
            "rew_sum": 0,
            "target_rew": 0,
            "num_steps": 0
        }
    
    restart_info = info_dict[f"restart_{info_dict['num_restart']:0>2}"]
    # ...rest of the function...
```

## Root Cause

The root cause is likely in the initialization of `info_dict`. In the `run` function in `env_interaction.py`, check that `num_restart` is properly initialized to 0 instead of -1:

```python
def run(args, cfg_fname, mode="navigate_env"):
    # ...existing code...
    
    info_dict = {
        "episode_ind": 0,
        "num_restart": 0,  # Ensure this is 0, not -1
        # ...other initializations...
    }
```

This fix will ensure the `num_restart` value is always valid when used to construct dictionary keys, preventing the KeyError.