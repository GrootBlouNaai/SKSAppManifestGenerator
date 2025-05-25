from os import environ
from src.sk_common.sk_libs.sk_gui_master import SKGuiMaster
from src.sks_appmanifest_generator.sk_run import SKSAppManifestGenerator
from src.sks_appmanifest_generator.sk_vars import APP_ICON_FPATH, APP_NAME

def run() -> None:
    environ['SK_SHOW_WINDOW'] = '0'
    SKGuiMaster.title(APP_NAME)
    SKGuiMaster.icon(APP_ICON_FPATH)
    v_sk_cl = SKSAppManifestGenerator()
    v_sk_cl.run()
if __name__ == '__main__':
    run()