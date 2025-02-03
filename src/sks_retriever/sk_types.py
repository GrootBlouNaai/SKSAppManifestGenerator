from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict
TYPE_INV_INFO = List[Any]
TYPE_STATS_INFO = Dict[(str, Any)]
TYPE_INFO_DATA = Dict[(str, Any)]
TYPE_INFO_OUT_DATA = Dict[(str, Any)]
TYPE_ACHS_DATA = List[Any]
TYPE_ACH_IMAGES_DATA = List[str]
TYPE_STATS_DATA = List[Any]
TYPE_INV_DATA = Dict[(str, Any)]
TYPE_APPMANIFEST_DATA = str
TYPE_APPMANIFEST_OUT_DATA = Dict[(str, Any)]
TYPE_APPID_DATA = Tuple[(
 TYPE_INFO_DATA,
 Optional[TYPE_ACHS_DATA],
 Optional[TYPE_STATS_DATA],
 Optional[TYPE_INV_DATA],
 Optional[TYPE_APPMANIFEST_DATA])]

class TYPE_APPID_OUTPUT_PATHS(TypedDict):
    root: Path
    controllers: Path
    achievement_images: Path
    info: Path
    achievements: Path
    stats: Path
    inventory: Path
    appmanifest: Path


class TYPE_APPID_CACHE_PATHS(TypedDict):
    root: Path
    info: Path
    stats: Path
    inventory: Path