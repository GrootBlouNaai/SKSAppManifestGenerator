from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from logging import error as lerror
from logging import info as linfo
from src.sk_common.sk_setup.sk_setup_logging import h_setup_logging
from src.sk_common.sk_utilities.sk_ensure_path import h_ensure_path
from src.sk_common.sk_utilities.sk_is_empty import h_is_empty
from src.sk_common.sk_utilities.sk_sanitize import h_sanitize_list
from src.sks_appmanifest_generator.sk_args import SKSAppManifestGeneratorArgs
from src.sks_appmanifest_generator.sk_vars import APP_CACHE_DPATH, APP_DATA_DPATH, APP_LOG_FPATH, APP_NAME, APP_OUTPUT_DPATH
from src.sks_retriever.sk_run import SKSRetriever

class SKSAppManifestGenerator:

    def __init__(self) -> None:
        self._command_line = self._setup_command_line()
        h_ensure_path(APP_DATA_DPATH)
        h_setup_logging(APP_LOG_FPATH, self._command_line.debug)

    def _get_fn_name(self, a_name: str) -> str:
        return f"[SKSAppManifestGenerator] [{a_name}]:"

    def run(self) -> None:
        __fn_name__ = self._get_fn_name('run')
        v_appids = h_sanitize_list(self._command_line.appid)
        v_sks_retriever_cl = v_appids + [
         '--appmanifest-mode',
         '--output',
         str(APP_OUTPUT_DPATH),
         '--cache-output',
         str(APP_CACHE_DPATH),
         '--retrieve-appmanifest',
         '--refresh-all']
        if self._command_line.login:
            if self._command_line.login_save:
                v_sks_retriever_cl.append('--login-save')
        else:
            v_sks_retriever_cl.append('--login-anonymous')
        if self._command_line.debug:
            v_sks_retriever_cl.append('--debug')
        v_sks_retriever = SKSRetriever(v_sks_retriever_cl, APP_NAME)
        _, v_sks_retriever_data_all = v_sks_retriever.run()
        if h_is_empty(v_sks_retriever_data_all):
            lerror('%s sksretriever -> unknown_error', __fn_name__)
        linfo('%s done', __fn_name__)

    def _setup_command_line(self) -> SKSAppManifestGeneratorArgs:
        v_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
        v_parser.add_argument('-l',
          '--login', help='Login with your Steam account.', default=False, action='store_true')
        v_parser.add_argument('-ls',
          '--login-save',
          help='You will no longer be prompted for your Steam login information.',
          default=False,
          action='store_true')
        v_parser.add_argument('-d', '--debug', help='Enable debug output.', default=False, action='store_true')
        v_parser.add_argument('appid', nargs='+', type=int)
        return v_parser.parse_args(namespace=SKSAppManifestGeneratorArgs)