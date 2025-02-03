from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from html import unescape
from json import loads as json_loads
from logging import error as lerror
from logging import info as linfo
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse
from requests import get as req_get
from vdf import dumps as vdf_dumps
from vdf import loads as vdf_loads
from src.sk_common.sk_setup.sk_setup_logging import h_setup_logging
from src.sk_common.sk_utilities.sk_ensure_path import h_ensure_path
from src.sk_common.sk_utilities.sk_is_empty import h_is_empty
from src.sk_common.sk_utilities.sk_read_file import h_read_file_text
from src.sk_common.sk_utilities.sk_sanitize import h_sanitize_list
from src.sk_common.sk_utilities.sk_write_file import h_write_file_binary, h_write_file_json, h_write_file_text
from src.sk_common.sk_vars import APP_IS_BUNDLED
from src.sks_retriever.sk_args import SKSRetrieverArgs
from src.sks_retriever.sk_helpers.sk_utilities import h_queue, h_strtobool
from src.sks_retriever.sk_libs.sks_client import SKSClient
from src.sks_retriever.sk_parsers.sk_appmanifest import h_parser_appmanifest
from src.sks_retriever.sk_parsers.sk_inventory import h_parser_inventory
from src.sks_retriever.sk_parsers.sk_stats import h_parser_stats
from src.sks_retriever.sk_types import TYPE_ACH_IMAGES_DATA, TYPE_ACHS_DATA, TYPE_APPID_CACHE_PATHS, TYPE_APPID_DATA, TYPE_APPID_OUTPUT_PATHS, TYPE_APPMANIFEST_DATA, TYPE_INFO_DATA, TYPE_INFO_OUT_DATA, TYPE_INV_DATA, TYPE_STATS_DATA
from src.sks_retriever.sk_vars import APP_CACHE_DPATH, APP_DATA_DPATH, APP_LOG_FPATH, APP_NAME, APP_OUTPUT_DPATH, APP_REQUESTS_HEADERS, APP_REQUESTS_TIMEOUT, APP_TOP_OWNERS_STEAMIDS

class SKSRetriever:

    def __init__(self, a_command_line: Optional[List[str]]=None, a_login_service: str=APP_NAME) -> None:
        self._external_mode = not h_is_empty(a_command_line)
        self._refresh_mode = False
        self._appmanifest_mode = False
        if a_command_line is not None and '--appmanifest-mode' in a_command_line:
            a_command_line.remove('--appmanifest-mode')
            self._appmanifest_mode = True
        self._command_line = self._setup_command_line(a_command_line)
        if self._command_line.retrieve_all:
            self._command_line.retrieve_dlc = True
            self._command_line.retrieve_achievement_images = True
            self._command_line.retrieve_achievements_stats = True
            self._command_line.retrieve_inventory = True
            self._command_line.retrieve_controller = True
            self._command_line.retrieve_appmanifest = True
        if self._command_line.retrieve_appmanifest:
            self._command_line.retrieve_dlc = True
        if not self._external_mode:
            h_ensure_path(APP_DATA_DPATH)
            h_setup_logging(APP_LOG_FPATH, self._command_line.debug)
        self._output_dpath = self._get_output_cache_dpath(self._command_line.output, APP_OUTPUT_DPATH)
        h_ensure_path(self._output_dpath)
        self._cache_dpath = self._get_output_cache_dpath(self._command_line.cache_output, APP_CACHE_DPATH)
        h_ensure_path(self._cache_dpath)
        self._sks_client = SKSClient(self._command_line.login_anonymous, self._command_line.login_save, a_login_service)

    def _get_output_cache_dpath(self, a_dir_dpath: Optional[str], a_default_dpath: Path) -> Path:
        if APP_IS_BUNDLED or self._external_mode:
            if a_dir_dpath is not None and (not h_is_empty(a_dir_dpath)):
                return Path(a_dir_dpath)
        return a_default_dpath

    def get_fn_name(self, a_name: str) -> str:
        return f'[SKSRetriever] [{a_name}]:'

    def run(self) -> Tuple[Optional[TYPE_APPID_DATA], List[TYPE_APPID_DATA]]:
        __fn_name__ = self.get_fn_name('run')
        v_appid_info_out = None
        v_appids_info_out = []
        v_appids_list = (self._command_line.appid if not h_is_empty(self._command_line.appid) else self._sks_client.get_app_list()) + self._command_line.append_appids
        v_appids = h_sanitize_list(v_appids_list)
        v_appids_count = len(v_appids)
        for v_appid_index, v_appid in enumerate(v_appids, 1):
            v_appid_int = int(v_appid)
            linfo('%s parse -> %s (%s/%s)', __fn_name__, v_appid, v_appid_index, v_appids_count)
            if v_appid_int in self._command_line.blacklist:
                linfo('%s skip -> blacklisted', __fn_name__)
                continue
            self._refresh_mode = self._command_line.refresh_all or v_appid_int in self._command_line.refresh_only
            linfo('%s refresh_mode -> %s', __fn_name__, self._refresh_mode)
            v_appid_info_out = self._get_appid_data(v_appid)
            if v_appid_info_out is not None:
                v_appids_info_out.append(v_appid_info_out)
                linfo('%s parse -> ok', __fn_name__)
            else:
                lerror('%s parse -> error', __fn_name__)
        linfo('%s done', __fn_name__)
        return (v_appid_info_out, v_appids_info_out)

    def _get_file_content(self, a_file_fpath: Path) -> Any:
        __fn_name__ = self.get_fn_name('_get_file_content')
        linfo('%s -> %s', __fn_name__, a_file_fpath)
        if not self._refresh_mode:
            if a_file_fpath.exists():
                v_file_ext = a_file_fpath.suffix
                if v_file_ext in '.jpg':
                    linfo('%s content -> ok -> %s', __fn_name__, a_file_fpath)
                    return ''
                v_file_content = h_read_file_text(a_file_fpath)
                if v_file_content is not None and (not h_is_empty(v_file_content)):
                    if v_file_ext in ['.vdf', '.acf']:
                        v_file_content = vdf_loads(v_file_content)
                    elif v_file_ext in '.json':
                        v_file_content = json_loads(v_file_content)
                    linfo('%s content -> ok -> %s', __fn_name__, a_file_fpath)
                    return v_file_content
                linfo('%s content -> empty -> %s', __fn_name__, a_file_fpath)
            else:
                linfo('%s content -> not_exists -> %s', __fn_name__, a_file_fpath)
        else:
            linfo('%s content -> refresh -> %s', __fn_name__, a_file_fpath)
        return False

    def _get_appid_output_paths(self, a_appid: str) -> TYPE_APPID_OUTPUT_PATHS:
        v_root_dpath = self._output_dpath / a_appid
        v_controllers_dpath = v_root_dpath / 'controllers'
        v_ach_imgs_dpath = v_root_dpath / 'achievement_images'
        v_info_fpath = v_root_dpath / 'info.json'
        v_achs_fpath = v_root_dpath / 'achievements.json'
        v_stats_fpath = v_root_dpath / 'stats.json'
        v_inv_fpath = v_root_dpath / 'inventory.json'
        v_appmanifest_fpath = v_root_dpath / f'appmanifest_{a_appid}.acf'
        return {'root': v_root_dpath, 'controllers': v_controllers_dpath, 'achievement_images': v_ach_imgs_dpath, 'info': v_info_fpath, 'achievements': v_achs_fpath, 'stats': v_stats_fpath, 'inventory': v_inv_fpath, 'appmanifest': v_appmanifest_fpath}

    def _get_appid_cache_paths(self, a_appid: str) -> TYPE_APPID_CACHE_PATHS:
        v_root_dpath = self._cache_dpath / a_appid
        v_info_fpath = v_root_dpath / 'get_product_info.json'
        v_stats_fpath = v_root_dpath / 'get_user_stats_info.json'
        v_inv_fpath = v_root_dpath / 'get_inventory_info.json'
        return {'root': v_root_dpath, 'info': v_info_fpath, 'stats': v_stats_fpath, 'inventory': v_inv_fpath}

    def _get_appid_data_fake(self, a_appid: str, a_appid_name: str, a_appid_type: str, a_appid_parent: Optional[str]) -> Dict[str, Any]:
        return {'appid': a_appid, 'common': {'name': a_appid_name, 'type': a_appid_type, 'parent': a_appid_parent}}

    def _get_appid_data(self, a_appid: str, a_appid_is_dlc: bool=False) -> Optional[TYPE_APPID_DATA]:
        __fn_name__ = self.get_fn_name('_get_appid_data')
        linfo('%s -> %s', __fn_name__, a_appid)
        v_c_paths = self._get_appid_cache_paths(a_appid)
        v_c_root_dpath = v_c_paths['root']
        v_c_info_fpath = v_c_paths['info']
        h_ensure_path(v_c_root_dpath)
        v_appid_file_info = self._get_file_content(v_c_info_fpath)
        if v_appid_file_info is False:
            v_appid_file_info = self._sks_client.get_product_info(int(a_appid))
            h_write_file_json(v_c_info_fpath, v_appid_file_info)
        if v_appid_file_info is not None and (not h_is_empty(v_appid_file_info)):
            if 'common' not in v_appid_file_info:
                v_appid_file_info = self._get_appid_data_fake(a_appid, f'{APP_NAME} Unknown App {a_appid}', 'dlc' if a_appid_is_dlc else 'unknown', None)
            return self._get_appid_info(a_appid, v_appid_file_info)
        lerror('%s sks_client -> get_product_info -> unknown_error', __fn_name__)

    def _get_appid_info(self, a_appid: str, a_appid_info: TYPE_INFO_DATA) -> TYPE_APPID_DATA:
        __fn_name__ = self.get_fn_name('_get_appid_info')
        v_o_paths = self._get_appid_output_paths(a_appid)
        v_o_root_dpath = v_o_paths['root']
        v_o_controllers_dpath = v_o_paths['controllers']
        v_o_ach_imgs_dpath = v_o_paths['achievement_images']
        v_o_achs_fpath = v_o_paths['achievements']
        v_o_stats_fpath = v_o_paths['stats']
        v_o_info_fpath = v_o_paths['info']
        v_o_inv_fpath = v_o_paths['inventory']
        v_o_appmanifest_fpath = v_o_paths['appmanifest']
        v_c_paths = self._get_appid_cache_paths(a_appid)
        v_c_stats_fpath = v_c_paths['stats']
        v_c_inv_fpath = v_c_paths['inventory']
        v_info_out = {}
        v_achs_out = None
        v_stats_out = None
        v_inv_out = None
        v_appmanifest_out = None
        self._parse_appid_common_info(a_appid, a_appid_info, v_info_out)
        v_info_type = v_info_out['Type']
        if not self._appmanifest_mode or (self._appmanifest_mode and v_info_type != 'dlc'):
            h_ensure_path(v_o_root_dpath)
        if v_info_type != 'dlc':
            self._parse_appid_info(a_appid, a_appid_info, v_info_out, v_o_controllers_dpath)
            if not self._appmanifest_mode:
                v_achs_out, v_stats_out = self._get_appid_achs_stats_info(a_appid, v_c_stats_fpath, v_o_achs_fpath, v_o_stats_fpath, v_o_ach_imgs_dpath)
                v_inv_out = self._get_appid_inventory_info(a_appid, v_c_inv_fpath, v_o_inv_fpath)
            v_appmanifest_out = self._parse_appid_appmanifest_info(a_appid, v_info_out, v_o_appmanifest_fpath)
        else:
            self._parse_appid_dlc_info(a_appid, a_appid_info, v_info_out)
        if not self._appmanifest_mode:
            h_write_file_json(v_o_info_fpath, v_info_out)
            linfo('%s written -> %s', __fn_name__, v_o_info_fpath)
        return (v_info_out, v_achs_out, v_stats_out, v_inv_out, v_appmanifest_out)

    def _get_dlc_info(self, a_appid: str, a_appid_parent: Optional[str]=None) -> Optional[TYPE_APPID_DATA]:
        __fn_name__ = self.get_fn_name('_get_dlc_info')
        linfo('%s -> %s', __fn_name__, a_appid)
        if self._command_line.retrieve_dlc:
            return self._get_appid_data(a_appid, True)
        linfo('%s not_enabled -> --retrieve-dlc', __fn_name__)
        return self._get_appid_info(a_appid, self._get_appid_data_fake(a_appid, f'{a_appid} - NO INFO (without --retrieve-dlc)', 'DLC', a_appid_parent))

    def _parse_appid_common_info(self, a_appid: str, a_appid_info: TYPE_INFO_DATA, a_appid_info_out: TYPE_INFO_OUT_DATA) -> TYPE_INFO_OUT_DATA:
        __fn_name__ = self.get_fn_name('_parse_appid_common_info')
        v_info_common = a_appid_info['common']
        linfo('%s -> %s', __fn_name__, a_appid)
        a_appid_info_out['AppId'] = int(a_appid)
        v_name = unescape(v_info_common['name']) if 'name' in v_info_common else None
        a_appid_info_out['Name'] = v_name
        linfo('%s name -> %s', __fn_name__, v_name)
        v_type = v_info_common['type'].lower() if 'type' in v_info_common else None
        a_appid_info_out['Type'] = v_type
        linfo('%s type -> %s', __fn_name__, v_type)
        v_oslist = v_info_common['oslist'].split(',') if 'oslist' in v_info_common and (not h_is_empty(v_info_common['oslist'])) else None
        a_appid_info_out['OsList'] = v_oslist
        linfo('%s oslist -> %s', __fn_name__, v_oslist)
        v_releasestate = v_info_common['releasestate'] if 'releasestate' in v_info_common else None
        a_appid_info_out['ReleaseState'] = v_releasestate
        linfo('%s releasestate -> %s', __fn_name__, v_releasestate)
        v_icon_image = None
        if 'icon' in v_info_common:
            v_icon_image_fname = v_info_common['icon']
            f'https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/{a_appid}0'
            v_icon_image = f'/{v_icon_image_fname}.jpg'
        a_appid_info_out['IconUrl'] = v_icon_image
        linfo('%s icon_image -> %s', __fn_name__, v_icon_image)
        v_header_image = None
        if 'header_image' in v_info_common and 'english' in v_info_common['header_image']:
            v_header_image_fname = v_info_common['header_image']['english']
            v_header_image = f'https://cdn.cloudflare.steamstatic.com/steam/apps/{a_appid}/{v_header_image_fname}0'
        a_appid_info_out['ImageUrl'] = v_header_image
        linfo('%s header_image -> %s', __fn_name__, v_header_image)
        v_depots = {}
        v_depots_shared = {}
        if 'depots' in a_appid_info:
            v_depots_info = a_appid_info['depots']
            for v_depot_id, v_depot_info in v_depots_info.items():
                if v_depot_id.isnumeric() and (not isinstance(v_depot_info, str)):
                    v_depot_id_str = str(v_depot_id)
                    linfo('%s parse -> %s', __fn_name__, v_depot_id_str)
                    v_depot_size = int(v_depot_info['manifests']['public']['size'] if 'manifests' in v_depot_info and 'public' in v_depot_info['manifests'] and ('size' in v_depot_info['manifests']['public']) else 0)
                    linfo('%s depot_size -> %s', __fn_name__, v_depot_size)
                    v_depot_manifestid = v_depot_info['manifests']['public']['gid'] if 'manifests' in v_depot_info and 'public' in v_depot_info['manifests'] and ('gid' in v_depot_info['manifests']['public']) else None
                    linfo('%s depot_manifestid -> %s', __fn_name__, v_depot_manifestid)
                    v_depot_os = v_depot_info['config']['oslist'] if 'config' in v_depot_info and 'oslist' in v_depot_info['config'] else None
                    linfo('%s depot_os -> %s', __fn_name__, v_depot_os)
                    v_depot_is_dlc = v_depot_info.get('dlcappid', None)
                    linfo('%s depot_is_dlc -> %s', __fn_name__, v_depot_is_dlc)
                    v_depot_is_shared_install = 'sharedinstall' in v_depot_info
                    linfo('%s depot_is_shared_install -> %s', __fn_name__, v_depot_is_shared_install)
                    if v_depot_os is None or 'windows' in v_depot_os.split(','):
                        if v_depot_is_shared_install and 'depotfromapp' in v_depot_info:
                            v_depots_shared[v_depot_id_str] = v_depot_info['depotfromapp']
                        elif v_depot_manifestid is not None:
                            if v_depot_is_dlc is not None:
                                v_depots[v_depot_id_str] = {'manifest': int(v_depot_manifestid), 'size': v_depot_size, 'dlcappid': int(v_depot_is_dlc)}
                            else:
                                v_depots[v_depot_id_str] = {'manifest': int(v_depot_manifestid), 'size': v_depot_size}
                        else:
                            linfo('%s depot_is_not_used', __fn_name__)
                    else:
                        linfo('%s depot_is_not_for_windows_os', __fn_name__)
        else:
            linfo('%s appid_no_depots', __fn_name__)
        a_appid_info_out['Depots'] = v_depots
        a_appid_info_out['DepotsShared'] = v_depots_shared
        linfo('%s depots -> %s', __fn_name__, v_depots.keys())
        linfo('%s depots_shared -> %s', __fn_name__, v_depots_shared.keys())
        return a_appid_info_out

    def _parse_appid_info(self, a_appid: str, a_appid_info: TYPE_INFO_DATA, a_appid_info_out: TYPE_INFO_OUT_DATA, a_o_controllers_dpath: Path) -> TYPE_INFO_OUT_DATA:
        __fn_name__ = self.get_fn_name('_parse_appid_info')
        v_info_common = a_appid_info['common']
        linfo('%s -> %s', __fn_name__, a_appid)
        v_launch = None
        if 'config' in a_appid_info and 'launch' in a_appid_info['config']:
            v_launch_config = a_appid_info['config']['launch']
            for v_launch_info in v_launch_config.values():
                if 'type' in v_launch_info and v_launch_info['type'] == 'default' and ('executable' in v_launch_info) and (not h_is_empty(v_launch_info['executable'])):
                    v_launch_exe = v_launch_info['executable'].strip()
                    if 'config' in v_launch_info and 'oslist' in v_launch_info['config'] and ('betakey' not in v_launch_info['config']):
                        v_launch_os = v_launch_info['config']['oslist']
                        if 'windows' in v_launch_os.split(','):
                            v_launch = v_launch_exe
                            break
            if v_launch is None:
                for v_launch_info in v_launch_config.values():
                    if 'executable' in v_launch_info and (not h_is_empty(v_launch_info['executable'])):
                        v_launch_exe = v_launch_info['executable'].strip()
                        if 'config' in v_launch_info and 'oslist' in v_launch_info['config'] and ('betakey' not in v_launch_info['config']):
                            v_launch_os = v_launch_info['config']['oslist']
                            if 'windows' in v_launch_os.split(','):
                                v_launch = v_launch_exe
                                break
                        else:
                            v_launch = v_launch_exe
                            break
        a_appid_info_out['Launch'] = v_launch
        linfo('%s launch -> %s', __fn_name__, v_launch)
        v_installdir = a_appid_info['config']['installdir'] if 'config' in a_appid_info and 'installdir' in a_appid_info['config'] else None
        a_appid_info_out['InstallDir'] = v_installdir
        linfo('%s installdir -> %s', __fn_name__, v_installdir)
        v_buildid = int(a_appid_info['depots']['branches']['public']['buildid']) if 'depots' in a_appid_info and 'branches' in a_appid_info['depots'] and ('public' in a_appid_info['depots']['branches']) and ('buildid' in a_appid_info['depots']['branches']['public']) else None
        a_appid_info_out['BuildId'] = v_buildid
        linfo('%s buildid -> %s', __fn_name__, v_buildid)
        v_languages = []
        if 'supported_languages' in v_info_common:
            v_languages_supported = v_info_common['supported_languages']
            for v_language_supported_key, v_language_supported_info in v_languages_supported.items():
                if 'supported' in v_language_supported_info and h_strtobool(v_language_supported_info['supported']):
                    v_languages.append(v_language_supported_key)
        a_appid_info_out['Languages'] = v_languages
        linfo('%s languages -> %s', __fn_name__, v_languages)
        v_dlcs = {}
        v_dlcs_extended = {}
        if 'extended' in a_appid_info and 'listofdlc' in a_appid_info['extended']:
            for v_dlc_id in a_appid_info['extended']['listofdlc'].split(','):
                if v_dlc_id not in v_dlcs:
                    v_dlc_info = self._get_dlc_info(v_dlc_id, a_appid)
                    if v_dlc_info is not None:
                        v_dlc_info_data = v_dlc_info[0]
                        v_dlc_info_depots = v_dlc_info_data['Depots']
                        if not h_is_empty(v_dlc_info_depots):
                            a_appid_info_out['Depots'].update(v_dlc_info_depots)
                        v_dlcs_extended[v_dlc_id] = v_dlc_info_data
        v_dlcs.update(v_dlcs_extended)
        linfo('%s dlcs_extended -> %s', __fn_name__, v_dlcs_extended.keys())
        v_dlcs_depots = {}
        if 'depots' in a_appid_info:
            v_depots_info = a_appid_info['depots']
            for v_depot_id, v_depot_info in v_depots_info.items():
                if v_depot_id.isnumeric() and 'dlcappid' in v_depot_info:
                    v_dlc_id = v_depot_info['dlcappid']
                    if a_appid != v_dlc_id and v_dlc_id not in v_dlcs:
                        v_dlc_info = self._get_dlc_info(v_dlc_id, a_appid)
                        if v_dlc_info is not None:
                            v_dlc_info_data = v_dlc_info[0]
                            v_dlc_info_depots = v_dlc_info_data['Depots']
                            if not h_is_empty(v_dlc_info_depots):
                                a_appid_info_out['Depots'].update(v_dlc_info_depots)
                            v_dlcs_depots[v_dlc_id] = v_dlc_info_data
        v_dlcs.update(v_dlcs_depots)
        linfo('%s dlcs_depots -> %s', __fn_name__, v_dlcs_depots.keys())
        a_appid_info_out['Dlc'] = v_dlcs
        linfo('%s dlcs -> %s', __fn_name__, v_dlcs.keys())
        linfo('%s append_depots -> %s', __fn_name__, a_appid_info_out['Depots'].keys())
        v_controllers = {}
        if 'config' in a_appid_info and 'steamcontrollerconfigdetails' in a_appid_info['config'] and (not isinstance(a_appid_info['config']['steamcontrollerconfigdetails'], str)):
            v_controllers_info = a_appid_info['config']['steamcontrollerconfigdetails']
            for v_controller_id, v_controller_info in v_controllers_info.items():
                v_controller_id_int = int(v_controller_id)
                v_controller_type = v_controller_info['controller_type']
                v_controller_enabled_branches = v_controller_info['enabled_branches']
                self._download_controller_vdf(v_controller_id_int, a_o_controllers_dpath)
                v_controllers.update({v_controller_id_int: {'Id': v_controller_id_int, 'Type': v_controller_type, 'Public': 'default' in v_controller_enabled_branches or 'public' in v_controller_enabled_branches}})
        else:
            linfo('%s appid_no_controllers', __fn_name__)
        a_appid_info_out['Controllers'] = v_controllers
        linfo('%s controllers -> %s', __fn_name__, v_controllers.keys())
        return a_appid_info_out

    def _parse_appid_dlc_info(self, a_appid: str, a_appid_info: TYPE_INFO_DATA, a_appid_info_out: TYPE_INFO_OUT_DATA) -> TYPE_INFO_OUT_DATA:
        __fn_name__ = self.get_fn_name('_parse_appid_dlc_info')
        v_info_common = a_appid_info['common']
        linfo('%s -> %s', __fn_name__, a_appid)
        v_parent = int(v_info_common['parent']) if 'parent' in v_info_common and v_info_common['parent'] is not None else None
        a_appid_info_out['MainAppId'] = v_parent
        linfo('%s parent -> %s', __fn_name__, v_parent)
        return a_appid_info_out

    def _parse_appid_appmanifest_info(self, a_appid: str, a_appid_info_out: TYPE_INFO_OUT_DATA, a_o_appmanifest_fpath: Path) -> Optional[TYPE_APPMANIFEST_DATA]:
        __fn_name__ = self.get_fn_name('_parse_appid_appmanifest_info')
        linfo('%s -> %s', __fn_name__, a_appid)
        v_appmanifest_out = None
        if self._command_line.retrieve_appmanifest:
            v_appmanifest_info = h_parser_appmanifest(self, a_appid_info_out, self._sks_client._login_steamid)
            v_appmanifest_out = vdf_dumps(v_appmanifest_info, pretty=True)
            v_appmanifest_out = v_appmanifest_out.replace('" "', '"\t\t"')
            h_write_file_text(a_o_appmanifest_fpath, v_appmanifest_out)
            linfo('%s written -> %s', __fn_name__, a_o_appmanifest_fpath)
        else:
            linfo('%s not_enabled -> --retrieve_appmanifest', __fn_name__)
        return v_appmanifest_out

    def _download_controller_vdf(self, a_controller_id: int, a_o_controllers_dpath: Path) -> None:
        __fn_name__ = self.get_fn_name('_download_controller_vdf')
        linfo('%s -> %s', __fn_name__, a_controller_id)
        if self._command_line.retrieve_controller:
            v_controller_fpath = a_o_controllers_dpath / f'{a_controller_id}.vdf'
            v_controller_content = self._get_file_content(v_controller_fpath)
            if v_controller_content is False:
                v_controller_content = self._sks_client.get_ugc_content(a_controller_id)
                if v_controller_content is not None:
                    h_ensure_path(a_o_controllers_dpath)
                    h_write_file_text(v_controller_fpath, v_controller_content)
                    linfo('%s written -> %s', __fn_name__, v_controller_fpath)
                else:
                    lerror('%s sks_client -> get_ugc_content -> unknown_error', __fn_name__)
        else:
            linfo('%s not_enabled -> --retrieve-controller', __fn_name__)

    def _download_achievement_images(self, a_ach_imgs: TYPE_ACH_IMAGES_DATA, a_o_ach_imgs_dpath: Path) -> None:
        __fn_name__ = self.get_fn_name('_download_achievement_images')
        if self._command_line.retrieve_achievement_images:
            h_ensure_path(a_o_ach_imgs_dpath)

            def _download_achievement_images_queue(a_quq: Queue) -> None:
                while not a_quq.empty():
                    v_ach_image_url = a_quq.get()
                    v_ach_image_name = Path(urlparse(v_ach_image_url).path).name
                    v_ach_image_save_to = a_o_ach_imgs_dpath / v_ach_image_name
                    v_ach_image_content = self._get_file_content(v_ach_image_save_to)
                    if v_ach_image_content is False:
                        v_ach_request = req_get(v_ach_image_url, timeout=APP_REQUESTS_TIMEOUT, headers=APP_REQUESTS_HEADERS)
                        if v_ach_request.status_code == 200:
                            h_write_file_binary(v_ach_image_save_to, v_ach_request.content)
                            linfo('%s written -> %s', __fn_name__, v_ach_image_save_to)
                        else:
                            lerror('%s error -> %s', __fn_name__, v_ach_image_url)
                    a_quq.task_done()
                linfo('%s done', __fn_name__)
            h_queue(a_ach_imgs, _download_achievement_images_queue)
        else:
            linfo('%s not_enabled -> --retrieve-achievement-images', __fn_name__)

    def _get_appid_achs_stats_info(self, a_appid: str, a_c_stats_fpath: Path, a_o_achs_fpath: Path, a_o_stats_fpath: Path, a_o_ach_imgs_dpath: Path) -> Tuple[Optional[TYPE_ACHS_DATA], Optional[TYPE_STATS_DATA]]:
        __fn_name__ = self.get_fn_name('_get_appid_achs_stats_info')
        linfo('%s -> %s', __fn_name__, a_appid)
        v_stats_out = None
        v_achs_out = None
        if self._command_line.retrieve_achievements_stats:
            v_stats_content = self._get_file_content(a_c_stats_fpath)
            if v_stats_content is False:
                v_top_owners_steamids = self._command_line.top_owners
                if self._sks_client._login_steamid is not None and (not h_is_empty(self._sks_client._login_steamid)):
                    v_top_owners_steamids.append(self._sks_client._login_steamid)
                for v_top_owner_steamid in v_top_owners_steamids:
                    linfo('%s get_user_game_stats -> %s', __fn_name__, v_top_owner_steamid)
                    v_stats_content = self._sks_client.get_user_game_stats(int(a_appid), v_top_owner_steamid)
                    if v_stats_content is not None:
                        h_write_file_json(a_c_stats_fpath, v_stats_content)
                        break
            if v_stats_content is not None and (not h_is_empty(v_stats_content)):
                v_achs_out, u_ach_imgs_out, v_stats_out = h_parser_stats(a_appid, v_stats_content, self._command_line.retrieve_achievement_images)
                if not h_is_empty(v_achs_out):
                    h_write_file_json(a_o_achs_fpath, v_achs_out)
                    linfo('%s written -> %s', __fn_name__, a_o_achs_fpath)
                    self._download_achievement_images(u_ach_imgs_out, a_o_ach_imgs_dpath)
                else:
                    linfo('%s appid_no_achievements', __fn_name__)
                if not h_is_empty(v_stats_out):
                    h_write_file_json(a_o_stats_fpath, v_stats_out)
                    linfo('%s written -> %s', __fn_name__, a_o_stats_fpath)
                else:
                    linfo('%s appid_no_stats', __fn_name__)
            else:
                h_write_file_json(a_c_stats_fpath, {})
                lerror('%s sks_client -> get_user_game_stats -> unknown_error', __fn_name__)
        else:
            linfo('%s not_enabled -> --retrieve-achievements-stats', __fn_name__)
        return (v_achs_out, v_stats_out)

    def _get_appid_inventory_info(self, a_appid: str, a_c_inv_fpath: Path, a_o_inv_fpath: Path) -> Optional[TYPE_INV_DATA]:
        __fn_name__ = self.get_fn_name('_get_appid_inventory_info')
        linfo('%s -> %s', __fn_name__, a_appid)
        v_inv_out = None
        if self._command_line.retrieve_inventory:
            v_inv_out = self._get_file_content(a_c_inv_fpath)
            if v_inv_out is False:
                v_inv_out = self._sks_client.get_inventory_info(int(a_appid))
                h_write_file_json(a_c_inv_fpath, v_inv_out)
            if v_inv_out is not None and (not h_is_empty(v_inv_out)):
                v_inv_out = h_parser_inventory(v_inv_out)
                if not h_is_empty(v_inv_out):
                    h_write_file_json(a_o_inv_fpath, v_inv_out)
                    linfo('%s written -> %s', __fn_name__, a_o_inv_fpath)
                else:
                    linfo('%s appid_no_inventory', __fn_name__)
            else:
                h_write_file_json(a_c_inv_fpath, [])
                lerror('%s sks_client -> get_inventory_info -> unknown_error', __fn_name__)
        else:
            linfo('%s not_enabled -> --retrieve-inventory', __fn_name__)
        return v_inv_out

    def _setup_command_line(self, a_command_line: Optional[Sequence[str]]) -> SKSRetrieverArgs:
        v_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
        v_parser.add_argument('-ls', '--login-save', help='You will no longer be prompted for your Steam login information.', default=False, action='store_true')
        v_parser.add_argument('-la', '--login-anonymous', help="You will be logged in as 'anonymous' but the game stats, inventory and achievements information will not be retrieved.", default=False, action='store_true')
        v_parser.add_argument('-o', '--output', help="Where to output your game definitions. By default it will output to 'SKSRetriever/_APPID_' directory.", default=None, type=str)
        v_parser.add_argument('-c', '--cache-output', help="Where to output the metadatas cache. By default it will output to '_APPDATA_/SKSRetriever/steam_cache' directory.", default=None, type=str)
        v_parser.add_argument('-ra', '--refresh-all', help='Disable cache and refresh data from Steam for all Steam apps.', default=False, action='store_true')
        v_parser.add_argument('-ro', '--refresh-only', help='Disable cache and refresh data from Steam only for specific Steam apps.', default=[], nargs='*', type=int)
        v_parser.add_argument('--blacklist', help='List of Steam apps to be excluded.', default=[], nargs='*', type=int)
        v_parser.add_argument('--top-owners', help='SteamIDs with public profiles that own a lot of games.', default=APP_TOP_OWNERS_STEAMIDS, nargs='*', type=int)
        v_parser.add_argument('--retrieve-all', help='Enable retrieval of all options.', default=False, action='store_true')
        v_parser.add_argument('--retrieve-dlc', help='Enable retrieval of dlc info.', default=False, action='store_true')
        v_parser.add_argument('--retrieve-achievement-images', help='Enable retrieval of achievement images.', default=False, action='store_true')
        v_parser.add_argument('--retrieve-achievements-stats', help='Enable retrieval of achievements and stats.', default=False, action='store_true')
        v_parser.add_argument('--retrieve-inventory', help='Enable retrieval of inventory.', default=False, action='store_true')
        v_parser.add_argument('--retrieve-controller', help='Enable retrieval of controller configurations.', default=False, action='store_true')
        v_parser.add_argument('--retrieve-appmanifest', help='Enable retrieval of appmanifest.acf', default=False, action='store_true')
        v_parser.add_argument('-d', '--debug', help='Enable debug output.', default=False, action='store_true')
        v_parser.add_argument('--append-appids', help='Add additional appids to retrieve data for.', default=[], nargs='*', type=int)
        v_parser.add_argument('appid', nargs='*', type=int)
        if self._external_mode:
            return v_parser.parse_args(a_command_line, namespace=SKSRetrieverArgs)
        return v_parser.parse_args(namespace=SKSRetrieverArgs)