import sys
from os.path import expandvars
from pathlib import Path
APP_ROOT_DPATH = Path.cwd()
APP_IS_BUNDLED = False
APP_PKG_ROOT_DPATH = Path(getattr(sys, '_MEIPASS', APP_ROOT_DPATH))
APP_GLOBAL_RESOURCES_DPATH = APP_PKG_ROOT_DPATH / 'sk_resources' if APP_IS_BUNDLED else APP_ROOT_DPATH / 'resources'
APP_GLOBAL_BIN_DPATH = APP_PKG_ROOT_DPATH / 'sk_bin' if APP_IS_BUNDLED else APP_ROOT_DPATH / 'bin'
APP_GLOBAL_BUILD_DPATH = APP_ROOT_DPATH / 'build'
APP_GLOBAL_DATA_DPATH = APP_ROOT_DPATH / 'data'
APP_GLOBAL_COMMON_DATA_DPATH = APP_GLOBAL_DATA_DPATH / 'Common'



def h_ensure_path(a_dir_dpath: Path) -> bool:
    if not a_dir_dpath.exists():
        a_dir_dpath.mkdir(parents=True)
        return True
    return False