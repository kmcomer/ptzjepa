# PTZJEPA Logging System

Yes, PTZJEPA produces several types of log files:

## 1. Standard Output Logs

The default approach uses standard output redirection:
```bash
python /app/main.py -rm lifelong [other args] 2>&1 | tee /path/to/log.out
```

This captures all Python logging output to a file specified after `tee`.

## 2. Python Logger Output

The system uses Python's logging module throughout the codebase:
```python
logger = logging.getLogger(__name__)
logger.info("interaction_complete: %s", interaction_complete)
```

Logging verbosity is controlled by the `--debug` flag.

## 3. Tracked Data Files

When running with `-tp` or `--track_all` flags, the system creates:
- `/persistence/collected_positions/*.csv` - Camera positioning data
- `/persistence/collected_commands/*.csv` - Action command history
- `/persistence/collected_embeds/*.npy` - Embedding vector logs

## 4. Model Checkpoints and Metrics

Training runs generate their own logs:
- `/persistence/world_models/*/logs/` - Training metrics
- `/persistence/agents/*/logs/` - Agent training history

## 5. Network and Timing Logs

If you implement the networking monitoring suggested earlier:
- `/persistence/network_metrics.csv` - Network performance data
- `/persistence/timing_logs.csv` - Stage timing information

You can view current logs using:
```bash
# View latest standard output log
tail -f /path/to/log.out

# List tracked positions
ls -la /persistence/collected_positions/
```