from pathlib import Path
from src.sk_common.sk_vars import APP_GLOBAL_RESOURCES_DPATH

def h_get_project_icon(a_resources_dpath: Path) -> Path:
    v_default_icon_fpath = APP_GLOBAL_RESOURCES_DPATH / 'default.ico'
    v_icon_fpath = a_resources_dpath / 'icon.ico'
    if v_icon_fpath.exists():
        return v_icon_fpath
    return v_default_icon_fpath