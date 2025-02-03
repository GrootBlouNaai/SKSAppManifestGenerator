from argparse import Namespace
from typing import List, Optional

class SKSRetrieverArgs(Namespace):
    login_save: bool
    login_anonymous: bool
    output: Optional[str]
    cache_output: Optional[str]
    refresh_all: bool
    refresh_only: List[int]
    blacklist: List[int]
    top_owners: List[int]
    retrieve_all: bool
    retrieve_dlc: bool
    retrieve_achievement_images: bool
    retrieve_achievements_stats: bool
    retrieve_inventory: bool
    retrieve_controller: bool
    retrieve_appmanifest: bool
    debug: bool
    append_appids: List[int]
    appid: List[int]