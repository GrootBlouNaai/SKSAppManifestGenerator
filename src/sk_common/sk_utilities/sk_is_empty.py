from typing import Any

def h_is_empty(a_value: Any) -> bool:
    if isinstance(a_value, (int, bool)):
        return False
    return a_value is None or len(a_value) == 0