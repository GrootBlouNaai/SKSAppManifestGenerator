from queue import Queue
from threading import Thread
from typing import Any, Callable, List

def h_strtobool(a_value: str) -> bool:
    return isinstance(a_value, str) and a_value.lower() in ('y', 'yes', 't', 'true',
                                                            'on', '1')


def h_queue(a_values: List[Any], a_target: Callable[([Queue], None)]) -> None:
    v_quq = Queue()
    for v_value in a_values:
        v_quq.put(v_value)
    else:
        Thread(target=a_target, args=(v_quq,), daemon=True).start()
        v_quq.join()