import os
import shutil
import subprocess
from typing import Optional


def _repo_root(cwd: str) -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=cwd, stderr=subprocess.DEVNULL)
        return out.decode("utf-8", errors="ignore").strip() or cwd
    except Exception:
        return cwd


def _user_home() -> str:
    return os.path.expanduser("~")


def resolve_target_dir(target: str, scope: str, cwd: str, roo_mode: Optional[str] = None) -> str:
    scope = scope or "project"
    if target == "codex":
        if scope == "user":
            base = os.environ.get("CODEX_HOME", os.path.join(_user_home(), ".codex"))
            return os.path.join(base, "skills")
        root = _repo_root(cwd)
        return os.path.join(root, ".codex", "skills")

    if target == "claude":
        if scope == "user":
            return os.path.join(_user_home(), ".claude", "skills")
        root = _repo_root(cwd)
        return os.path.join(root, ".claude", "skills")

    if target == "opencode":
        if scope == "user":
            preferred = os.path.join(_user_home(), ".config", "opencode", "skill")
            alt = os.path.join(_user_home(), ".config", "opencode", "skills")
            return alt if os.path.exists(alt) else preferred
        root = _repo_root(cwd)
        preferred = os.path.join(root, ".opencode", "skill")
        alt = os.path.join(root, ".opencode", "skills")
        return alt if os.path.exists(alt) else preferred

    if target == "amp":
        if scope == "user":
            return os.path.join(_user_home(), ".config", "agents", "skills")
        root = _repo_root(cwd)
        return os.path.join(root, ".agents", "skills")

    if target == "roo":
        mode = roo_mode or "skills"
        if scope == "user":
            return os.path.join(_user_home(), ".roo", mode)
        root = _repo_root(cwd)
        return os.path.join(root, ".roo", mode)

    if target == "cursor":
        if scope == "user":
            raise RuntimeError("cursor user-scope rules are not file-based; use project scope")
        root = _repo_root(cwd)
        return os.path.join(root, ".cursor", "rules")

    return os.path.abspath(cwd)


def _read_skill_body(skill_md_path: str) -> str:
    with open(skill_md_path, "r", encoding="utf-8") as f:
        text = f.read()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def install_skill(
    output_root: str,
    skill_name: str,
    target: str,
    scope: str,
    target_dir: Optional[str],
    overwrite: bool,
    roo_mode: Optional[str],
    cwd: str,
) -> str:
    if target == "generic":
        return output_root

    scope = "user"
    if target == "cursor":
        scope = "project"

    resolved_dir = target_dir or resolve_target_dir(target, scope, cwd, roo_mode)

    if target == "cursor":
        os.makedirs(resolved_dir, exist_ok=True)
        rule_path = os.path.join(resolved_dir, f"{skill_name}.mdc")
        if os.path.exists(rule_path) and not overwrite:
            raise RuntimeError(f"target file exists: {rule_path}")
        body = _read_skill_body(os.path.join(output_root, "SKILL.md"))
        content = (
            "---\n"
            f"description: {skill_name} skill\n"
            "globs: []\n"
            "alwaysApply: false\n"
            "---\n\n"
            f"{body}\n\n"
            f"References are available at: {output_root}\\references\\INDEX.md\n"
        )
        with open(rule_path, "w", encoding="utf-8") as f:
            f.write(content)
        return rule_path

    dest = os.path.join(resolved_dir, skill_name)
    if os.path.exists(dest):
        if not overwrite:
            manifest_path = os.path.join(dest, "manifest.json")
            if not os.path.exists(manifest_path):
                raise RuntimeError(f"target directory exists: {dest}")
        shutil.rmtree(dest)
    os.makedirs(resolved_dir, exist_ok=True)
    shutil.copytree(output_root, dest)
    return dest
