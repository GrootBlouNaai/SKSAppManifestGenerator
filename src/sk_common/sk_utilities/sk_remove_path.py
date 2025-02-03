from pathlib import Path
from shutil import rmtree

def h_remove_path(a_path: Path) -> bool:
    if a_path.exists():
        if a_path.is_dir():
            rmtree(a_path)
        else:
            a_path.unlink()
        return True
    return False