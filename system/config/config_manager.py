"""Configuration management system with SHA256 hash registry and timestamped backups.

Provides atomic config file operations with:
- Automatic SHA256 hash computation and registry tracking
- Timestamped backups before modifications (YYYYMMDD_HHMMSS format)
- JSON-based hash registry (config_hash_registry.json)
"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

BACKUP_FILENAME_MIN_PARTS = 4


class ConfigManager:
    """Manages configuration files with hash tracking and automatic backups."""

    def __init__(self, config_root: Path | None = None) -> None:
        """Initialize config manager.

        Args:
            config_root: Root directory for config files. Defaults to system/config.
        """
        if config_root is None:
            config_root = Path(__file__).parent
        self.config_root = Path(config_root)
        self.backup_dir = self.config_root / ".backup"
        self.registry_file = self.config_root / "config_hash_registry.json"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        for subdir in ["calibration", "questionnaire", "environments"]:
            (self.config_root / subdir).mkdir(parents=True, exist_ok=True)

    def _compute_sha256(self, file_path: Path) -> str:
        """Compute SHA256 hash of file.

        Args:
            file_path: Path to file to hash

        Returns:
            Hexadecimal SHA256 hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _load_registry(self) -> dict[str, Any]:  # type: ignore[misc]
        """Load hash registry from disk.

        Returns:
            Registry dictionary with file paths as keys
        """
        if not self.registry_file.exists():
            return {}
        with open(self.registry_file) as f:
            return json.load(f)  # type: ignore[no-any-return]

    def _save_registry(self, registry: dict[str, Any]) -> None:  # type: ignore[misc]
        """Save hash registry to disk.

        Args:
            registry: Registry dictionary to save
        """
        with open(self.registry_file, "w") as f:
            json.dump(registry, f, indent=2, sort_keys=True)

    def _create_backup(self, file_path: Path) -> Path | None:
        """Create timestamped backup of config file.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file, or None if source doesn't exist
        """
        if not file_path.exists():
            return None

        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        microseconds = now.strftime("%f")
        relative_path = file_path.relative_to(self.config_root)
        backup_name = (
            f"{timestamp}_{microseconds}_{relative_path.as_posix().replace('/', '_')}"
        )
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        return backup_path

    def _update_registry(self, file_path: Path) -> None:
        """Update hash registry for a file.

        Args:
            file_path: Path to file to register
        """
        if not file_path.exists():
            return

        registry = self._load_registry()
        relative_path = str(file_path.relative_to(self.config_root))
        hash_value = self._compute_sha256(file_path)

        registry[relative_path] = {
            "hash": hash_value,
            "last_modified": datetime.now().isoformat(),
            "size_bytes": file_path.stat().st_size,
        }

        self._save_registry(registry)

    def save_config(
        self, relative_path: str, content: str, create_backup: bool = True
    ) -> Path:
        """Save configuration file with automatic backup and hash registry update.

        Args:
            relative_path: Path relative to config root (e.g., 'calibration/model.json')
            content: Content to write to file
            create_backup: Whether to create backup before modification

        Returns:
            Path to saved config file
        """
        file_path = self.config_root / relative_path

        if create_backup and file_path.exists():
            self._create_backup(file_path)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        self._update_registry(file_path)

        return file_path

    def save_config_json(  # type: ignore[misc]
        self, relative_path: str, data: Any, create_backup: bool = True
    ) -> Path:
        """Save JSON configuration file with automatic backup and hash registry update.

        Args:
            relative_path: Path relative to config root (e.g., 'calibration/model.json')
            data: Data to serialize to JSON
            create_backup: Whether to create backup before modification

        Returns:
            Path to saved config file
        """
        content = json.dumps(data, indent=2, sort_keys=True)
        return self.save_config(relative_path, content, create_backup=create_backup)

    def load_config(self, relative_path: str) -> str:
        """Load configuration file content.

        Args:
            relative_path: Path relative to config root

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        file_path = self.config_root / relative_path
        return file_path.read_text(encoding="utf-8")

    def load_config_json(self, relative_path: str) -> Any:  # type: ignore[misc]
        """Load JSON configuration file.

        Args:
            relative_path: Path relative to config root

        Returns:
            Parsed JSON data

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        content = self.load_config(relative_path)
        return json.loads(content)

    def verify_hash(self, relative_path: str) -> bool:
        """Verify file hash matches registry.

        Args:
            relative_path: Path relative to config root

        Returns:
            True if hash matches registry, False otherwise
        """
        file_path = self.config_root / relative_path
        if not file_path.exists():
            return False

        registry = self._load_registry()
        if relative_path not in registry:
            return False

        current_hash = self._compute_sha256(file_path)
        return current_hash == registry[relative_path]["hash"]  # type: ignore[no-any-return]

    def get_file_info(self, relative_path: str) -> dict[str, Any] | None:  # type: ignore[misc]
        """Get registry information for a file.

        Args:
            relative_path: Path relative to config root

        Returns:
            Registry entry dict or None if not registered
        """
        registry = self._load_registry()
        return registry.get(relative_path)

    def list_backups(self, relative_path: str | None = None) -> list[Path]:
        """List backup files.

        Args:
            relative_path: Optional filter for specific config file

        Returns:
            List of backup file paths, sorted by timestamp (newest first)
        """
        backups = []
        pattern = (
            "*" if relative_path is None else f"*_{relative_path.replace('/', '_')}"
        )

        for backup_file in self.backup_dir.glob(pattern):
            if backup_file.is_file():
                backups.append(backup_file)

        return sorted(backups, reverse=True)

    def restore_backup(self, backup_path: Path, create_backup: bool = True) -> Path:
        """Restore configuration from backup.

        Args:
            backup_path: Path to backup file
            create_backup: Whether to backup current file before restore

        Returns:
            Path to restored config file

        Raises:
            ValueError: If backup path format is invalid
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        backup_name = backup_path.name
        if "_" not in backup_name:
            raise ValueError(f"Invalid backup filename format: {backup_name}")

        parts = backup_name.split("_", 3)
        if len(parts) < BACKUP_FILENAME_MIN_PARTS:
            raise ValueError(f"Invalid backup filename format: {backup_name}")

        encoded_path = parts[3]
        registry = self._load_registry()

        relative_path = None
        for path in registry:
            if path.replace("/", "_") == encoded_path:
                relative_path = path
                break

        if relative_path is None:
            relative_path = encoded_path.replace("_", "/")

        file_path = self.config_root / relative_path

        if create_backup and file_path.exists():
            self._create_backup(file_path)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, file_path)

        self._update_registry(file_path)

        return file_path

    def get_registry(self) -> dict[str, Any]:  # type: ignore[misc]
        """Get complete hash registry.

        Returns:
            Registry dictionary
        """
        return self._load_registry()

    def rebuild_registry(self) -> dict[str, Any]:  # type: ignore[misc]
        """Rebuild hash registry by scanning all config files.

        Returns:
            Updated registry dictionary
        """
        registry = {}
        for pattern in ["**/*.json", "**/*.yaml", "**/*.yml", "**/*.toml"]:
            for file_path in self.config_root.glob(pattern):
                if file_path.is_file() and ".backup" not in file_path.parts:
                    relative_path = str(file_path.relative_to(self.config_root))
                    hash_value = self._compute_sha256(file_path)
                    registry[relative_path] = {
                        "hash": hash_value,
                        "last_modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                        "size_bytes": file_path.stat().st_size,
                    }

        self._save_registry(registry)
        return registry
