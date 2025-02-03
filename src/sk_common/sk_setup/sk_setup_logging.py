from datetime import datetime
from logging import FileHandler, Formatter, getLogger
from os import path
from pathlib import Path
from colorlog import ColoredFormatter, StreamHandler
from src.sk_common.sk_utilities.sk_ensure_path import h_ensure_path
from src.sk_common.sk_utilities.sk_remove_path import h_remove_path

def h_setup_logging(a_file_fpath: Path, a_debug: bool=False) -> None:
    v_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    v_file_dpath = a_file_fpath.parent
    v_file_date_fpath = v_file_dpath / f"{a_file_fpath.stem}_{v_date}{a_file_fpath.suffix}"
    v_file_current_fpath = v_file_dpath / f"{a_file_fpath.stem}_current{a_file_fpath.suffix}"
    h_ensure_path(v_file_dpath)
    h_remove_path(v_file_current_fpath)
    v_log_level = 'DEBUG' if a_debug else 'INFO'
    v_log_file_format = '[%(asctime)s] [%(levelname)-8s] %(message)s'
    v_log_console_format = '[%(asctime)s] [%(log_color)s%(levelname)-8s%(reset)s] %(message)s'
    v_log = getLogger()
    v_log.setLevel(v_log_level)
    v_log_stream_handler = StreamHandler()
    v_log_stream_handler.setFormatter(ColoredFormatter(v_log_console_format))
    v_log.addHandler(v_log_stream_handler)
    v_log_file_handler = FileHandler(v_file_date_fpath, encoding='utf-8')
    v_log_file_handler.setFormatter(Formatter(v_log_file_format))
    v_log.addHandler(v_log_file_handler)
    if a_debug:
        v_log_current_file_handler = FileHandler(v_file_current_fpath, encoding='utf-8')
        v_log_current_file_handler.setFormatter(Formatter(v_log_file_format))
        v_log.addHandler(v_log_current_file_handler)
    v_logs_limit = 5
    v_logs_glob = v_file_dpath.glob('*.log')
    v_logs_glob_sorted = sorted(v_logs_glob, key=(path.getmtime))
    for v_log_glob_path in v_logs_glob_sorted[:-v_logs_limit]:
        h_remove_path(v_log_glob_path)