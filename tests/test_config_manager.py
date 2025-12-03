"""Tests for configuration management system."""

import json
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from system.config.config_manager import ConfigManager


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def config_manager(temp_config_dir):
    """Create ConfigManager instance for testing."""
    return ConfigManager(config_root=temp_config_dir)


class TestConfigManager:
    """Test suite for ConfigManager."""

    def test_init_creates_directories(self, temp_config_dir):
        """Test that initialization creates required directories."""
        ConfigManager(config_root=temp_config_dir)

        assert (temp_config_dir / ".backup").exists()
        assert (temp_config_dir / "calibration").exists()
        assert (temp_config_dir / "questionnaire").exists()
        assert (temp_config_dir / "environments").exists()

    def test_save_config_creates_file(self, config_manager, temp_config_dir):
        """Test saving configuration file."""
        content = "test content"
        file_path = config_manager.save_config("test/config.txt", content)

        assert file_path.exists()
        assert file_path.read_text() == content

    def test_save_config_json(self, config_manager, temp_config_dir):
        """Test saving JSON configuration."""
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        file_path = config_manager.save_config_json("test/config.json", data)

        assert file_path.exists()
        loaded_data = json.loads(file_path.read_text())
        assert loaded_data == data

    def test_save_updates_registry(self, config_manager, temp_config_dir):
        """Test that saving a file updates the hash registry."""
        config_manager.save_config("test/file.txt", "content")

        registry = config_manager.get_registry()
        assert "test/file.txt" in registry
        assert "hash" in registry["test/file.txt"]
        assert "last_modified" in registry["test/file.txt"]
        assert "size_bytes" in registry["test/file.txt"]

    def test_hash_computation_deterministic(self, config_manager, temp_config_dir):
        """Test that SHA256 hash computation is deterministic."""
        content = "test content for hashing"
        config_manager.save_config("test/hash.txt", content)

        info1 = config_manager.get_file_info("test/hash.txt")
        config_manager.save_config("test/hash.txt", content, create_backup=False)
        info2 = config_manager.get_file_info("test/hash.txt")

        assert info1["hash"] == info2["hash"]

    def test_hash_changes_on_modification(self, config_manager, temp_config_dir):
        """Test that hash changes when file is modified."""
        config_manager.save_config("test/file.txt", "original content")
        original_hash = config_manager.get_file_info("test/file.txt")["hash"]

        config_manager.save_config("test/file.txt", "modified content")
        modified_hash = config_manager.get_file_info("test/file.txt")["hash"]

        assert original_hash != modified_hash

    def test_backup_created_on_save(self, config_manager, temp_config_dir):
        """Test that backup is created before modification."""
        config_manager.save_config("test/file.txt", "original")
        time.sleep(0.001)
        config_manager.save_config("test/file.txt", "modified")

        backups = config_manager.list_backups("test/file.txt")
        assert len(backups) >= 1

        backup_content = backups[0].read_text()
        assert backup_content == "original"

    def test_backup_filename_format(self, config_manager, temp_config_dir):
        """Test that backup filenames follow YYYYMMDD_HHMMSS_microseconds format."""
        config_manager.save_config("calibration/model.json", '{"test": true}')
        time.sleep(0.001)
        config_manager.save_config("calibration/model.json", '{"test": false}')

        backups = config_manager.list_backups("calibration/model.json")
        assert len(backups) >= 1

        backup_name = backups[0].name
        parts = backup_name.split("_")
        timestamp_part = parts[0] + "_" + parts[1]

        try:
            datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
        except ValueError:
            pytest.fail(
                f"Backup filename doesn't match YYYYMMDD_HHMMSS_microseconds format: {backup_name}"
            )

    def test_no_backup_on_first_save(self, config_manager, temp_config_dir):
        """Test that no backup is created for new files."""
        config_manager.save_config("test/new.txt", "first save")

        backups = config_manager.list_backups("test/new.txt")
        assert len(backups) == 0

    def test_load_config(self, config_manager, temp_config_dir):
        """Test loading configuration file."""
        content = "test content"
        config_manager.save_config("test/file.txt", content)

        loaded_content = config_manager.load_config("test/file.txt")
        assert loaded_content == content

    def test_load_config_json(self, config_manager, temp_config_dir):
        """Test loading JSON configuration."""
        data = {"key": "value", "list": [1, 2, 3]}
        config_manager.save_config_json("test/data.json", data)

        loaded_data = config_manager.load_config_json("test/data.json")
        assert loaded_data == data

    def test_verify_hash_valid(self, config_manager, temp_config_dir):
        """Test hash verification for unchanged file."""
        config_manager.save_config("test/file.txt", "content")
        assert config_manager.verify_hash("test/file.txt") is True

    def test_verify_hash_invalid_after_external_modification(
        self, config_manager, temp_config_dir
    ):
        """Test hash verification fails after external modification."""
        file_path = config_manager.save_config("test/file.txt", "original")

        file_path.write_text("externally modified")

        assert config_manager.verify_hash("test/file.txt") is False

    def test_verify_hash_nonexistent_file(self, config_manager, temp_config_dir):
        """Test hash verification for nonexistent file."""
        assert config_manager.verify_hash("nonexistent.txt") is False

    def test_list_backups_sorted_by_timestamp(self, config_manager, temp_config_dir):
        """Test that backups are sorted with newest first."""
        config_manager.save_config("test/file.txt", "version 1")
        time.sleep(0.001)
        config_manager.save_config("test/file.txt", "version 2")
        time.sleep(0.001)
        config_manager.save_config("test/file.txt", "version 3")

        backups = config_manager.list_backups("test/file.txt")
        assert len(backups) >= 2

        for i in range(len(backups) - 1):
            assert backups[i].name > backups[i + 1].name

    def test_list_backups_all(self, config_manager, temp_config_dir):
        """Test listing all backups without filter."""
        config_manager.save_config("file1.txt", "content")
        config_manager.save_config("file1.txt", "modified")

        config_manager.save_config("file2.txt", "content")
        config_manager.save_config("file2.txt", "modified")

        all_backups = config_manager.list_backups()
        assert len(all_backups) >= 2

    def test_restore_backup(self, config_manager, temp_config_dir):
        """Test restoring from backup."""
        original_content = "original version"
        config_manager.save_config("test/file.txt", original_content)
        time.sleep(0.001)

        config_manager.save_config("test/file.txt", "modified version")

        backups = config_manager.list_backups("test/file.txt")
        config_manager.restore_backup(backups[0])

        restored_content = config_manager.load_config("test/file.txt")
        assert restored_content == original_content

    def test_restore_creates_backup(self, config_manager, temp_config_dir):
        """Test that restore creates backup of current version."""
        config_manager.save_config("test/file.txt", "version 1")
        time.sleep(0.001)
        config_manager.save_config("test/file.txt", "version 2")

        backups_before = len(config_manager.list_backups("test/file.txt"))

        first_backup = config_manager.list_backups("test/file.txt")[-1]
        config_manager.restore_backup(first_backup)

        backups_after = len(config_manager.list_backups("test/file.txt"))
        assert backups_after == backups_before + 1

    def test_rebuild_registry(self, config_manager, temp_config_dir):
        """Test rebuilding hash registry from disk."""
        config_manager.save_config("file1.json", '{"a": 1}')
        config_manager.save_config("file2.yaml", "key: value")

        registry_file = temp_config_dir / "config_hash_registry.json"
        registry_file.unlink()

        rebuilt_registry = config_manager.rebuild_registry()

        assert "file1.json" in rebuilt_registry
        assert "file2.yaml" in rebuilt_registry

    def test_get_file_info_nonexistent(self, config_manager, temp_config_dir):
        """Test getting info for nonexistent file."""
        info = config_manager.get_file_info("nonexistent.txt")
        assert info is None

    def test_registry_persistence(self, temp_config_dir):
        """Test that registry persists across manager instances."""
        manager1 = ConfigManager(config_root=temp_config_dir)
        manager1.save_config("test/file.txt", "content")
        original_hash = manager1.get_file_info("test/file.txt")["hash"]

        manager2 = ConfigManager(config_root=temp_config_dir)
        loaded_hash = manager2.get_file_info("test/file.txt")["hash"]

        assert original_hash == loaded_hash

    def test_save_without_backup(self, config_manager, temp_config_dir):
        """Test saving without creating backup."""
        config_manager.save_config("test/file.txt", "original")
        config_manager.save_config("test/file.txt", "modified", create_backup=False)

        backups = config_manager.list_backups("test/file.txt")
        assert len(backups) == 0

    def test_nested_directory_creation(self, config_manager, temp_config_dir):
        """Test that nested directories are created automatically."""
        config_manager.save_config("a/b/c/deep.json", '{"nested": true}')

        file_path = temp_config_dir / "a/b/c/deep.json"
        assert file_path.exists()

    def test_json_sorted_keys(self, config_manager, temp_config_dir):
        """Test that JSON is saved with sorted keys."""
        data = {"z": 1, "a": 2, "m": 3}
        file_path = config_manager.save_config_json("test/sorted.json", data)

        content = file_path.read_text()
        assert content.index('"a"') < content.index('"m"') < content.index('"z"')

    def test_unicode_content_handling(self, config_manager, temp_config_dir):
        """Test handling of Unicode content."""
        content = "Hello 世界 🌍"
        config_manager.save_config("test/unicode.txt", content)

        loaded = config_manager.load_config("test/unicode.txt")
        assert loaded == content
