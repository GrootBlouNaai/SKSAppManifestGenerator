from typing import Any, Dict, List
from natsort import natsorted

def h_sanitize_list(a_values: List[Any], a_type: type=str) -> List[Any]:
    v_set = set(a_values)
    v_map = map(a_type, v_set)
    v_list = list(v_map)
    v_sort = natsorted(v_list)
    return v_sort


def h_sanitize_dict(a_values: Dict[(str, Any)]) -> Dict[(str, Any)]:
    v_dict = {}
    v_sort = natsorted(a_values.items())
    for v_dict_key, v_dict_value in v_sort:
        v_dict[v_dict_key] = v_dict_value
    else:
        return v_dict