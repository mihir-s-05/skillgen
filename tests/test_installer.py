from pathlib import Path

import pytest

from skillgen.installer import install_skill, resolve_install_dir


def _make_output_root(tmp_path: Path) -> Path:
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "SKILL.md").write_text("# Test Skill\n\nBody\n", encoding="utf-8")
    return out


def test_resolve_install_dir_defaults_to_agents(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("skillgen.installer.os.path.expanduser", lambda _: str(tmp_path))
    assert resolve_install_dir(for_claude=False) == str(tmp_path / ".agents" / "skills")
    assert resolve_install_dir(for_claude=True) == str(tmp_path / ".claude" / "skills")


def test_install_skill_writes_to_agents_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("skillgen.installer.os.path.expanduser", lambda _: str(tmp_path))
    output_root = _make_output_root(tmp_path / "gen")

    install_path = Path(install_skill(str(output_root), "myskill"))
    assert install_path == tmp_path / ".agents" / "skills" / "myskill"
    assert (install_path / "SKILL.md").exists()


def test_install_skill_writes_to_claude_when_requested(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("skillgen.installer.os.path.expanduser", lambda _: str(tmp_path))
    output_root = _make_output_root(tmp_path / "gen")

    install_path = Path(install_skill(str(output_root), "myskill", for_claude=True))
    assert install_path == tmp_path / ".claude" / "skills" / "myskill"
    assert (install_path / "SKILL.md").exists()


def test_install_skill_overwrites_existing_destination(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("skillgen.installer.os.path.expanduser", lambda _: str(tmp_path))
    output_root = _make_output_root(tmp_path / "gen")

    first = Path(install_skill(str(output_root), "myskill"))
    (first / "old.txt").write_text("old", encoding="utf-8")

    second = Path(install_skill(str(output_root), "myskill"))
    assert second.exists()
    assert not (second / "old.txt").exists()


def test_install_skill_noop_when_source_equals_destination(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("skillgen.installer.os.path.expanduser", lambda _: str(tmp_path))
    dest = tmp_path / ".agents" / "skills" / "myskill"
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / "SKILL.md"
    marker.write_text("# Existing\n", encoding="utf-8")

    result = Path(install_skill(str(dest), "myskill"))
    assert result == dest
    assert marker.exists()
