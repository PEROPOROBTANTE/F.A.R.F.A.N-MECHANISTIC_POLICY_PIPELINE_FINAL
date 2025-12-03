#!/usr/bin/env python3
"""Command-line interface for configuration management.

Usage examples:
    # Save a config file
    python config_cli.py save calibration/model.json --data '{"model": "test"}'

    # Load a config file
    python config_cli.py load calibration/model.json

    # Verify file hash
    python config_cli.py verify calibration/model.json

    # List backups
    python config_cli.py backups calibration/model.json

    # Restore from backup
    python config_cli.py restore .backup/20231201_143000_calibration_model.json

    # Show registry
    python config_cli.py registry

    # Rebuild registry
    python config_cli.py rebuild
"""

import argparse
import json
import sys
from pathlib import Path

from config_manager import ConfigManager


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Configuration management with hash tracking and backups"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    save_parser = subparsers.add_parser("save", help="Save configuration file")
    save_parser.add_argument("path", help="Relative path to config file")
    save_parser.add_argument("--data", help="JSON data to save", required=True)
    save_parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup creation"
    )

    load_parser = subparsers.add_parser("load", help="Load configuration file")
    load_parser.add_argument("path", help="Relative path to config file")
    load_parser.add_argument("--json", action="store_true", help="Parse as JSON")

    verify_parser = subparsers.add_parser("verify", help="Verify file hash")
    verify_parser.add_argument("path", help="Relative path to config file")

    info_parser = subparsers.add_parser("info", help="Show file information")
    info_parser.add_argument("path", help="Relative path to config file")

    backups_parser = subparsers.add_parser("backups", help="List backups")
    backups_parser.add_argument("path", nargs="?", help="Optional path filter")

    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup", help="Backup file name or path")
    restore_parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup of current version"
    )

    subparsers.add_parser("registry", help="Show hash registry")

    subparsers.add_parser("rebuild", help="Rebuild hash registry")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    manager = ConfigManager()

    try:
        if args.command == "save":
            try:
                data = json.loads(args.data)
                file_path = manager.save_config_json(
                    args.path, data, create_backup=not args.no_backup
                )
            except json.JSONDecodeError:
                file_path = manager.save_config(
                    args.path, args.data, create_backup=not args.no_backup
                )
            print(f"Saved: {file_path}")
            info = manager.get_file_info(args.path)
            print(f"Hash: {info['hash']}")

        elif args.command == "load":
            if args.json:
                data = manager.load_config_json(args.path)
                print(json.dumps(data, indent=2))
            else:
                content = manager.load_config(args.path)
                print(content)

        elif args.command == "verify":
            is_valid = manager.verify_hash(args.path)
            if is_valid:
                print(f"✓ Hash verification passed: {args.path}")
                return 0
            else:
                print(f"✗ Hash verification failed: {args.path}", file=sys.stderr)
                return 1

        elif args.command == "info":
            info = manager.get_file_info(args.path)
            if info is None:
                print(f"File not in registry: {args.path}", file=sys.stderr)
                return 1
            print(json.dumps(info, indent=2))

        elif args.command == "backups":
            backups = manager.list_backups(args.path)
            if not backups:
                print("No backups found")
            else:
                print(f"Found {len(backups)} backup(s):")
                for backup in backups:
                    print(f"  {backup.name}")

        elif args.command == "restore":
            backup_path = Path(args.backup)
            if not backup_path.is_absolute():
                backup_path = manager.backup_dir / args.backup

            restored_path = manager.restore_backup(
                backup_path, create_backup=not args.no_backup
            )
            print(f"Restored: {restored_path}")
            info = manager.get_file_info(
                str(restored_path.relative_to(manager.config_root))
            )
            print(f"Hash: {info['hash']}")

        elif args.command == "registry":
            registry = manager.get_registry()
            print(json.dumps(registry, indent=2))

        elif args.command == "rebuild":
            print("Rebuilding hash registry...")
            registry = manager.rebuild_registry()
            print(f"Registered {len(registry)} file(s)")
            for path in sorted(registry.keys()):
                print(f"  {path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
