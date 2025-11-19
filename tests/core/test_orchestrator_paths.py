from __future__ import annotations

from pathlib import Path

from saaaaaa.core.orchestrator.core import resolve_workspace_path


def test_resolve_workspace_path_prefers_project_root(tmp_path: Path) -> None:
    project_root = tmp_path / "workspace"
    rules_dir = project_root / "config" / "rules"
    module_dir = project_root / "src" / "saaaaaa" / "core" / "orchestrator"

    target_dir = project_root / "resources"
    target_dir.mkdir(parents=True)
    rules_dir.mkdir(parents=True)
    module_dir.mkdir(parents=True)

    expected = target_dir / "foo.txt"
    expected.write_text("demo", encoding="utf-8")

    resolved = resolve_workspace_path(
        "resources/foo.txt",
        project_root=project_root,
        rules_dir=rules_dir,
        module_dir=module_dir,
    )

    assert resolved == expected


def test_resolve_workspace_path_falls_back_to_rules_metodos(tmp_path: Path) -> None:
    project_root = tmp_path / "workspace"
    rules_dir = project_root / "config" / "rules"
    metodos_dir = rules_dir / "METODOS"
    module_dir = project_root / "src" / "saaaaaa" / "core" / "orchestrator"

    metodos_dir.mkdir(parents=True)
    module_dir.mkdir(parents=True)

    expected = metodos_dir / "custom_rule.json"
    expected.write_text("{}", encoding="utf-8")

    resolved = resolve_workspace_path(
        "custom_rule.json",
        project_root=project_root,
        rules_dir=rules_dir,
        module_dir=module_dir,
    )

    assert resolved == expected


def test_resolve_workspace_path_accepts_absolute_paths(tmp_path: Path) -> None:
    absolute_file = tmp_path / "absolute.json"
    absolute_file.write_text("{}", encoding="utf-8")

    assert resolve_workspace_path(absolute_file) == absolute_file
