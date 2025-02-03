import sys
from os.path import expandvars
from pathlib import Path
from src.sk_common.sk_utilities.sk_ensure_path import h_ensure_path
OS_WIN_APPDATA = Path(expandvars('%APPDATA%'))
APP_IS_BUNDLED = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
APP_IS_X64 = sys.maxsize > 4294967296
APP_ARCH = 'x64' if APP_IS_X64 else 'x32'
APP_ROOT_DPATH = Path.cwd()
APP_PKG_ROOT_DPATH = Path(getattr(sys, '_MEIPASS', APP_ROOT_DPATH))
APP_GLOBAL_RESOURCES_DPATH = APP_PKG_ROOT_DPATH / 'sk_resources' if APP_IS_BUNDLED else APP_ROOT_DPATH / 'resources'
APP_GLOBAL_BIN_DPATH = APP_PKG_ROOT_DPATH / 'sk_bin' if APP_IS_BUNDLED else APP_ROOT_DPATH / 'bin'
APP_GLOBAL_BUILD_DPATH = APP_ROOT_DPATH / 'build'
APP_GLOBAL_DATA_DPATH = APP_ROOT_DPATH / 'data'
APP_GLOBAL_COMMON_DATA_DPATH = APP_GLOBAL_DATA_DPATH / 'Common'
if not APP_IS_BUNDLED:
    h_ensure_path(APP_GLOBAL_COMMON_DATA_DPATH)