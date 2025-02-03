def h_ensure_path(a_dir_dpath: Path) -> bool:
    if not a_dir_dpath.exists():
        a_dir_dpath.mkdir(parents=True)
        return True
    return False