from json import loads as json_loads
from pathlib import Path
from typing import Any, Dict, Optional
from tomli import loads as toml_loads
from src.sk_common.sk_utilities.sk_is_empty import h_is_empty

def h_read_file_text(a_file_path: Path, a_encoding: str='utf-8') -> Optional[str]:
    if a_file_path.is_file():
        return a_file_path.read_text(encoding=a_encoding)


def h_read_file_json(a_file_path: Path, a_encoding: str='utf-8') -> Optional[Any]:
    v_raw = h_read_file_text(a_file_path, a_encoding)
    if v_raw is not None:
        if not h_is_empty(v_raw):
            return json_loads(v_raw)


def h_read_file_toml(a_file_path: Path, a_encoding: str='utf-8') -> Optional[Dict[(str, Any)]]:
    v_raw = h_read_file_text(a_file_path, a_encoding)
    if v_raw is not None:
        if not h_is_empty(v_raw):
            return toml_loads(v_raw)