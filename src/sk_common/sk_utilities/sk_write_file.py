from json import dumps as json_dumps
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def h_write_file_text(a_file_path: Path, a_file_raw: str) -> None:
    a_file_path.write_text((str(a_file_raw)), encoding='utf-8')


def h_write_file_json(a_file_path: Path, a_file_raw: Optional[Union[(List[Any], Dict[(str, Any)])]], a_minify: bool=False) -> None:
    a_file_path.write_text(json_dumps(a_file_raw,
      indent=(None if a_minify else 4)),
      encoding='utf-8')


def h_write_file_binary(a_file_path: Path, a_file_raw: bytes) -> None:
    a_file_path.write_bytes(a_file_raw)