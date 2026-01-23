from pathlib import Path

import pytest

from skillgen.installer import install_skill


def _make_output_root(tmp_path: Path) -> Path:
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "SKILL.md").write_text("# Test Skill\n\nBody\n", encoding="utf-8")
    return out


def test_install_skill_codex_project_scope_installs_under_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    output_root = _make_output_root(tmp_path / "gen")

    install_path = install_skill(
        str(output_root),
        "myskill",
        target="codex",
        scope="project",
        target_dir=None,
        overwrite=True,
        roo_mode=None,
        cwd=str(project),
    )

    expected = project / ".codex" / "skills" / "myskill"
    assert Path(install_path) == expected
    assert (expected / "SKILL.md").exists()


def test_install_skill_codex_user_scope_uses_CODEX_HOME(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    project = tmp_path / "project"
    project.mkdir()
    output_root = _make_output_root(tmp_path / "gen")

    install_path = install_skill(
        str(output_root),
        "myskill",
        target="codex",
        scope="user",
        target_dir=None,
        overwrite=True,
        roo_mode=None,
        cwd=str(project),
    )

    expected = codex_home / "skills" / "myskill"
    assert Path(install_path) == expected
    assert (expected / "SKILL.md").exists()


def test_install_skill_refuses_to_overwrite_when_overwrite_false(tmp_path: Path) -> None:
    output_root = _make_output_root(tmp_path / "gen")
    target_dir = tmp_path / "install-root"
    target_dir.mkdir()

    first = install_skill(
        str(output_root),
        "myskill",
        target="claude",
        scope="project",
        target_dir=str(target_dir),
        overwrite=True,
        roo_mode=None,
        cwd=str(tmp_path),
    )
    assert Path(first).exists()

    with pytest.raises(RuntimeError, match="target directory exists"):
        install_skill(
            str(output_root),
            "myskill",
            target="claude",
            scope="project",
            target_dir=str(target_dir),
            overwrite=False,
            roo_mode=None,
            cwd=str(tmp_path),
        )


def test_install_skill_cursor_requires_project_scope_and_honors_overwrite(tmp_path: Path) -> None:
    output_root = _make_output_root(tmp_path / "gen")
    rules_dir = tmp_path / "cursor-rules"
    rules_dir.mkdir()

    with pytest.raises(RuntimeError, match="cursor install requires project scope"):
        install_skill(
            str(output_root),
            "myskill",
            target="cursor",
            scope="user",
            target_dir=str(rules_dir),
            overwrite=False,
            roo_mode=None,
            cwd=str(tmp_path),
        )

    rule_path = Path(
        install_skill(
            str(output_root),
            "myskill",
            target="cursor",
            scope="project",
            target_dir=str(rules_dir),
            overwrite=False,
            roo_mode=None,
            cwd=str(tmp_path),
        )
    )
    assert rule_path.exists()

    with pytest.raises(RuntimeError, match="target file exists"):
        install_skill(
            str(output_root),
            "myskill",
            target="cursor",
            scope="project",
            target_dir=str(rules_dir),
            overwrite=False,
            roo_mode=None,
            cwd=str(tmp_path),
        )

    rule_path2 = Path(
        install_skill(
            str(output_root),
            "myskill",
            target="cursor",
            scope="project",
            target_dir=str(rules_dir),
            overwrite=True,
            roo_mode=None,
            cwd=str(tmp_path),
        )
    )
    assert rule_path2.exists()
