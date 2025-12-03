"""Example usage of the configuration management system."""


from config_manager import ConfigManager


def main() -> None:
    """Demonstrate config manager usage."""
    manager = ConfigManager()

    calibration_config = {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "thresholds": {"low": 0.3, "medium": 0.6, "high": 0.9},
    }

    print("=== Saving Configuration ===")
    config_path = manager.save_config_json(
        "calibration/model_config.json", calibration_config
    )
    print(f"Saved to: {config_path}")

    info = manager.get_file_info("calibration/model_config.json")
    print(f"Hash: {info['hash'][:16]}...")
    print(f"Size: {info['size_bytes']} bytes")

    print("\n=== Modifying Configuration ===")
    calibration_config["temperature"] = 0.8
    manager.save_config_json("calibration/model_config.json", calibration_config)
    print("Configuration updated (backup created automatically)")

    print("\n=== Listing Backups ===")
    backups = manager.list_backups("calibration/model_config.json")
    print(f"Found {len(backups)} backup(s):")
    for backup in backups:
        print(f"  - {backup.name}")

    print("\n=== Hash Verification ===")
    is_valid = manager.verify_hash("calibration/model_config.json")
    print(f"Hash verification: {'✓ PASS' if is_valid else '✗ FAIL'}")

    print("\n=== Loading Configuration ===")
    loaded_config = manager.load_config_json("calibration/model_config.json")
    print(f"Temperature: {loaded_config['temperature']}")
    print(f"Thresholds: {loaded_config['thresholds']}")

    print("\n=== Registry Summary ===")
    registry = manager.get_registry()
    print(f"Total registered files: {len(registry)}")
    for path in registry:
        print(f"  - {path}")

    print("\n=== Environment Config Example ===")
    env_config = {
        "environment": "production",
        "database_url": "postgresql://prod-server/db",
        "cache_ttl": 3600,
        "debug": False,
    }
    manager.save_config_json("environments/production.json", env_config)
    print("Environment configuration saved")

    print("\n=== Questionnaire Config Example ===")
    questionnaire_config = {
        "version": "2.0",
        "questions": [
            {
                "id": "PA01",
                "category": "Policy Alignment",
                "weight": 1.0,
            },
            {
                "id": "PA02",
                "category": "Policy Alignment",
                "weight": 0.8,
            },
        ],
    }
    manager.save_config_json(
        "questionnaire/questionnaire_v2.json", questionnaire_config
    )
    print("Questionnaire configuration saved")

    print("\n=== Final Registry ===")
    final_registry = manager.get_registry()
    print(f"Total files: {len(final_registry)}")
    for path, info in final_registry.items():
        print(f"  {path}")
        print(f"    Hash: {info['hash'][:16]}...")
        print(f"    Modified: {info['last_modified']}")
        print(f"    Size: {info['size_bytes']} bytes")


if __name__ == "__main__":
    main()
