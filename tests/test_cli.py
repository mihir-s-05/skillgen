import os
import subprocess
import sys
from pathlib import Path


def test_cli_rejects_removed_exclude_optional_flag():
    fixture = Path(__file__).parent / "fixtures" / "llms_sample.txt"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "skillgen",
            str(fixture),
            "--exclude-optional",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "unrecognized arguments" in proc.stderr.lower()


def _run_cli(args, env=None):
    return subprocess.run(
        [sys.executable, "-m", "skillgen", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def _read_description_and_keywords(skill_md: Path):
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    desc = []
    in_desc = False
    for line in lines:
        stripped = line.strip()
        if stripped == "description: |":
            in_desc = True
            continue
        if in_desc and stripped == "---":
            break
        if in_desc and stripped:
            desc.append(stripped)

    idx = lines.index("# Trigger keywords")
    keywords = [k.strip() for k in lines[idx + 1].split(",") if k.strip()]
    return " ".join(desc), keywords


def test_cli_help_shows_simplified_surface():
    proc = _run_cli(["--help"])
    assert proc.returncode == 0
    out = proc.stdout
    assert "--include-optional" in out
    assert "--no-snapshot" in out
    assert "--allow-external" in out
    assert "--heuristic-level" in out
    assert "--claude" in out
    assert "--target" not in out
    assert "--scope" not in out
    assert "--keyword-mode" not in out
    assert "--llm-model" not in out
    assert "--max-pages" not in out


def test_cli_installs_to_agents_by_default(tmp_path: Path):
    fixture = Path(__file__).parent / "fixtures" / "llms_sample.txt"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "out"
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)

    proc = _run_cli([str(fixture), "--out", str(out_dir), "--name", "cli-default", "--no-snapshot"], env=env)
    assert proc.returncode == 0
    assert (home / ".agents" / "skills" / "cli-default" / "SKILL.md").exists()


def test_cli_installs_to_claude_when_requested(tmp_path: Path):
    fixture = Path(__file__).parent / "fixtures" / "llms_sample.txt"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "out"
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)

    proc = _run_cli([str(fixture), "--out", str(out_dir), "--name", "cli-claude", "--no-snapshot", "--claude"], env=env)
    assert proc.returncode == 0
    assert (home / ".claude" / "skills" / "cli-claude" / "SKILL.md").exists()


def test_cli_heuristic_level_changes_description_not_keywords(tmp_path: Path):
    fixture = Path(__file__).parent / "fixtures" / "llms_sample.txt"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "out"
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)

    compact = _run_cli(
        [
            str(fixture),
            "--out",
            str(out_dir),
            "--name",
            "cli-compact",
            "--no-snapshot",
            "--heuristic-level",
            "compact",
        ],
        env=env,
    )
    verbose = _run_cli(
        [
            str(fixture),
            "--out",
            str(out_dir),
            "--name",
            "cli-verbose",
            "--no-snapshot",
            "--heuristic-level",
            "verbose",
        ],
        env=env,
    )
    assert compact.returncode == 0
    assert verbose.returncode == 0

    compact_desc, compact_keywords = _read_description_and_keywords(out_dir / "cli-compact" / "SKILL.md")
    verbose_desc, verbose_keywords = _read_description_and_keywords(out_dir / "cli-verbose" / "SKILL.md")

    assert compact_keywords == verbose_keywords
    assert compact_desc != verbose_desc
    assert "Covers:" in compact_desc
    assert "Useful navigation anchors include" in verbose_desc
