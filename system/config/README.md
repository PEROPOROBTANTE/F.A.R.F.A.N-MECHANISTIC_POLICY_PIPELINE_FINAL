# Configuration Management System

Atomic configuration file management with SHA256 hash registry and timestamped backups.

## Directory Structure

```
system/config/
├── calibration/         # Calibration configuration files
├── questionnaire/       # Questionnaire configuration files
├── environments/        # Environment-specific configurations
├── .backup/            # Timestamped backup files (YYYYMMDD_HHMMSS)
├── config_hash_registry.json  # SHA256 hash registry
├── config_manager.py   # Core configuration manager
├── config_cli.py       # Command-line interface
└── README.md          # This file
```

## Features

### 1. SHA256 Hash Registry
- Automatic hash computation on every save
- Hash verification to detect external modifications
- Registry stored in `config_hash_registry.json`
- Tracks hash, last_modified timestamp, and file size

### 2. Timestamped Backups
- Automatic backup before modifications (YYYYMMDD_HHMMSS_microseconds format)
- Backups stored in `.backup/` directory
- Backup filename format: `{YYYYMMDD}_{HHMMSS}_{microseconds}_{relative_path_with_underscores}`
- Microsecond precision ensures unique backups even for rapid updates
- Optional backup suppression for performance-critical operations

### 3. Atomic Operations
- Fail-safe file operations
- Registry updates only after successful writes
- Automatic directory creation

## Usage

### Python API

```python
from system.config.config_manager import ConfigManager

# Initialize manager
manager = ConfigManager()

# Save JSON configuration
data = {"model": "gpt-4", "temperature": 0.7}
manager.save_config_json("calibration/model.json", data)

# Save text configuration
manager.save_config("environments/prod.yaml", yaml_content)

# Load configuration
data = manager.load_config_json("calibration/model.json")
content = manager.load_config("environments/prod.yaml")

# Verify hash integrity
if manager.verify_hash("calibration/model.json"):
    print("File integrity verified")

# Get file information
info = manager.get_file_info("calibration/model.json")
print(f"Hash: {info['hash']}")
print(f"Modified: {info['last_modified']}")

# List backups
backups = manager.list_backups("calibration/model.json")
for backup in backups:
    print(backup.name)

# Restore from backup
manager.restore_backup(backups[0])

# Rebuild registry from disk
manager.rebuild_registry()
```

### Command-Line Interface

```bash
cd system/config

# Save configuration
python config_cli.py save calibration/model.json --data '{"model": "test"}'

# Load configuration
python config_cli.py load calibration/model.json --json

# Verify hash
python config_cli.py verify calibration/model.json

# Show file info
python config_cli.py info calibration/model.json

# List all backups
python config_cli.py backups

# List backups for specific file
python config_cli.py backups calibration/model.json

# Restore from backup
python config_cli.py restore 20231201_143000_calibration_model.json

# Show full registry
python config_cli.py registry

# Rebuild registry
python config_cli.py rebuild
```

## Hash Registry Format

```json
{
  "calibration/model.json": {
    "hash": "a3f7b2c1...",
    "last_modified": "2023-12-01T14:30:00.123456",
    "size_bytes": 1024
  },
  "questionnaire/config.json": {
    "hash": "d4e8f9a2...",
    "last_modified": "2023-12-01T15:45:00.789012",
    "size_bytes": 2048
  }
}
```

## Backup Filename Convention

Format: `{YYYYMMDD}_{HHMMSS}_{microseconds}_{relative_path_with_underscores}`

Examples:
- `20231201_143000_123456_calibration_model.json`
- `20231201_154530_789012_questionnaire_config.json`
- `20231202_091500_456789_environments_prod.yaml`

## Integration Examples

### With Calibration System

```python
from system.config.config_manager import ConfigManager

manager = ConfigManager()

# Load calibration config
calibration_config = manager.load_config_json("calibration/intrinsic_params.json")

# Modify and save with automatic backup
calibration_config["threshold"] = 0.85
manager.save_config_json("calibration/intrinsic_params.json", calibration_config)

# Verify integrity before critical operations
if not manager.verify_hash("calibration/intrinsic_params.json"):
    raise ValueError("Calibration config was modified externally!")
```

### With Environment Configurations

```python
manager = ConfigManager()

# Save environment-specific config
prod_config = {
    "database_url": "postgresql://prod-server/db",
    "cache_ttl": 3600,
    "debug": False
}
manager.save_config_json("environments/production.json", prod_config)

# List all environment configs
registry = manager.get_registry()
env_configs = [k for k in registry.keys() if k.startswith("environments/")]
```

## Security Considerations

1. **Hash Verification**: Always verify hashes before loading critical configs
2. **Backup Retention**: Implement periodic cleanup of old backups
3. **Access Control**: Ensure `.backup/` directory has appropriate permissions
4. **Sensitive Data**: Do not commit registry or backups containing secrets

## Performance Notes

- Hash computation uses 4KB chunks for memory efficiency
- Registry loads are cached in memory during operations
- Backup creation can be disabled for high-frequency updates
- Use `create_backup=False` when performance is critical

## Error Handling

```python
try:
    data = manager.load_config_json("missing.json")
except FileNotFoundError:
    print("Config file not found")

try:
    manager.restore_backup(Path("invalid_backup.json"))
except ValueError as e:
    print(f"Invalid backup format: {e}")
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_config_manager.py -v
```

## Maintenance

### Rebuild Registry

If the registry becomes corrupted or out of sync:

```python
manager = ConfigManager()
registry = manager.rebuild_registry()
```

### Clean Old Backups

```python
from datetime import datetime, timedelta

manager = ConfigManager()
threshold = datetime.now() - timedelta(days=30)

for backup in manager.list_backups():
    timestamp_str = "_".join(backup.name.split("_")[:2])
    backup_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    if backup_time < threshold:
        backup.unlink()
```

## Migration Guide

To migrate existing configs to this system:

```python
from pathlib import Path
from system.config.config_manager import ConfigManager

manager = ConfigManager()

# Scan for existing configs
for config_file in Path("old_config_dir").glob("**/*.json"):
    relative_path = config_file.relative_to("old_config_dir")
    content = config_file.read_text()
    
    # Import with initial hash registration (no backup)
    manager.save_config(str(relative_path), content, create_backup=False)
```
