import os
import shutil


def resolve_install_dir(for_claude: bool = False) -> str:
    home = os.path.expanduser("~")
    if for_claude:
        return os.path.join(home, ".claude", "skills")
    return os.path.join(home, ".agents", "skills")


def install_skill(output_root: str, skill_name: str, for_claude: bool = False) -> str:
    resolved_dir = resolve_install_dir(for_claude=for_claude)
    os.makedirs(resolved_dir, exist_ok=True)
    dest = os.path.join(resolved_dir, skill_name)
    src_real = os.path.normcase(os.path.abspath(output_root))
    dest_real = os.path.normcase(os.path.abspath(dest))
    if src_real == dest_real:
        return dest

    if os.path.exists(dest):
        shutil.rmtree(dest)

    shutil.copytree(output_root, dest)
    return dest
