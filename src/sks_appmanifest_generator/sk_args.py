from argparse import Namespace
from typing import List

class SKSAppManifestGeneratorArgs(Namespace):
    debug: bool
    login: bool
    login_save: bool
    appid: List[int]