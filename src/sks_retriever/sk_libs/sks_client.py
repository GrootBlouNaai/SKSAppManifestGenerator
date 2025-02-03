from json import loads as json_loads
from logging import error as lerror
from logging import info as linfo
from time import sleep, time
from typing import Any, Dict, List, Optional
from gevent import Timeout
from keyring import delete_password, get_credential, set_password
from keyring.errors import PasswordDeleteError
from requests import Response
from requests import get as req_get
from steam.client import SteamClient
from steam.core.msg import MsgProto
from steam.enums import EResult
from steam.enums.emsg import EMsg
from vdf import binary_loads as vdf_binary_loads
from src.sk_common.sk_libs.sk_gui_master import SKGuiMaster
from src.sk_common.sk_utilities.sk_is_empty import h_is_empty
from src.sks_retriever.sk_vars import APP_NAME, APP_REQUESTS_HEADERS, APP_REQUESTS_TIMEOUT, APP_STEAM_SENTRY_DPATH

class SKSClient:

    def __init__(self, a_login_anonymous: bool, a_login_save: bool, a_login_service: str) -> None:
        self._login_anonymous = a_login_anonymous
        self._login_save = a_login_save
        self._login_service = a_login_service
        self._login_attempt = False
        self._login_username = None
        self._login_password = None
        self._login_steamid = None
        self._request_last_time = time()
        self._request_sleep = 60
        self._instance = SteamClient()
        self._instance.set_credential_location(APP_STEAM_SENTRY_DPATH)

    def _get_fn_name(self, a_name: str) -> str:
        return f'[SKSClient] [{a_name}]:'

    def _request_get(self, a_url: str, a_url_params: Optional[Dict[str, Any]]=None, a_timeout: bool=True) -> Response:
        __fn_name__ = self._get_fn_name('_request_get')
        linfo('%s -> %s', __fn_name__, a_url)
        if a_timeout:
            v_diff_time = int(time() - self._request_last_time)
            if v_diff_time > self._request_sleep:
                linfo('%s one_request_per_minute_please_wait', __fn_name__)
                sleep(self._request_sleep)
        self._request_last_time = time()
        return req_get(a_url, a_url_params, timeout=APP_REQUESTS_TIMEOUT, headers=APP_REQUESTS_HEADERS)

    def _request_get_steam(self, a_interface_method: str, a_interface_version: int, a_url_params: Optional[Dict[str, Any]]=None):
        v_interface, v_method = a_interface_method.split('.')
        v_url = f'https://api.steampowered.com/{v_interface}/{v_method}/v{a_interface_version}'
        return self._request_get(v_url, a_url_params=a_url_params)

    def _user_login(self) -> EResult:
        __fn_name__ = self._get_fn_name('_user_login')
        v_prompt_no_input = 'You have not entered any input, you will need to relaunch the app to login again.'
        v_prompt_username = None
        v_prompt_password = None
        v_prompt_auth_code = v_prompt_two_factor_code = None
        v_prompt_for_unavailable = True
        v_get_credentials = get_credential(self._login_service, None)
        if v_get_credentials is not None:
            if self._login_save:
                if not h_is_empty(v_get_credentials.username) and (not h_is_empty(v_get_credentials.password)):
                    v_prompt_username = v_get_credentials.username
                    v_prompt_password = v_get_credentials.password
                    linfo('%s saved_credentials -> found', __fn_name__)
            elif not h_is_empty(v_get_credentials.username):
                v_prompt_delete_credentials = SKGuiMaster.askyesno(APP_NAME, 'I noticed that you previously saved the credentials but the save login setting is disabled, do you want to delete them?')
                if v_prompt_delete_credentials:
                    try:
                        delete_password(self._login_service, v_get_credentials.username)
                        linfo('%s saved_credentials -> deleted', __fn_name__)
                    except PasswordDeleteError:
                        lerror('%s error -> saved_credentials -> not_deleted', __fn_name__)
        else:
            linfo('%s saved_credentials -> not_found', __fn_name__)
        if h_is_empty(v_prompt_username) or h_is_empty(v_prompt_password):
            v_prompt_username = SKGuiMaster.askstring(APP_NAME, 'Enter username:')
            v_prompt_password = SKGuiMaster.askstring(APP_NAME, 'Enter password:', True)
        if h_is_empty(v_prompt_username) or h_is_empty(v_prompt_password):
            SKGuiMaster.showwarning(APP_NAME, v_prompt_no_input)
            return EResult.Fail
        v_login_result = self._instance.login(v_prompt_username, v_prompt_password)
        while v_login_result in [EResult.InvalidPassword, EResult.AccountLogonDenied, EResult.InvalidLoginAuthCode, EResult.AccountLoginDeniedNeedTwoFactor, EResult.TwoFactorCodeMismatch, EResult.TryAnotherCM, EResult.ServiceUnavailable]:
            sleep(0.1)
            if v_login_result == EResult.InvalidPassword:
                v_prompt_password_p = f'Invalid password for {v_prompt_username}. Enter password:'
                v_prompt_password = SKGuiMaster.askstring(APP_NAME, v_prompt_password_p, True)
                if h_is_empty(v_prompt_password):
                    SKGuiMaster.showwarning(APP_NAME, v_prompt_no_input)
                    break
            elif v_login_result in (EResult.AccountLogonDenied, EResult.InvalidLoginAuthCode):
                v_prompt_auth_code_p = 'Enter email code:' if v_login_result == EResult.AccountLogonDenied else 'Incorrect code. Enter email code:'
                v_prompt_auth_code, v_prompt_two_factor_code = (SKGuiMaster.askstring(APP_NAME, v_prompt_auth_code_p), None)
                if h_is_empty(v_prompt_auth_code):
                    SKGuiMaster.showwarning(APP_NAME, v_prompt_no_input)
                    break
            elif v_login_result in (EResult.AccountLoginDeniedNeedTwoFactor, EResult.TwoFactorCodeMismatch):
                prompt_two_factor_code_p = 'Enter 2FA code:' if v_login_result == EResult.AccountLoginDeniedNeedTwoFactor else 'Incorrect code. Enter 2FA code:'
                v_prompt_auth_code, v_prompt_two_factor_code = (None, SKGuiMaster.askstring(APP_NAME, prompt_two_factor_code_p))
                if h_is_empty(v_prompt_two_factor_code):
                    SKGuiMaster.showwarning(APP_NAME, v_prompt_no_input)
                    break
            elif v_login_result in (EResult.TryAnotherCM, EResult.ServiceUnavailable):
                if v_prompt_for_unavailable and v_login_result == EResult.ServiceUnavailable:
                    v_prompt_for_unavailable = False
                    v_prompt_keep_retrying = SKGuiMaster.askyesno(APP_NAME, 'Steam is down. Keep retrying?')
                    if not v_prompt_keep_retrying:
                        break
                self._instance.reconnect(maxdelay=15)
            v_login_result = self._instance.login(v_prompt_username, v_prompt_password, None, v_prompt_auth_code, v_prompt_two_factor_code)
        if self._login_save:
            if v_login_result == EResult.OK:
                set_password(self._login_service, v_prompt_username, v_prompt_password)
                linfo('%s credentials -> saved', __fn_name__)
            else:
                try:
                    delete_password(self._login_service, v_prompt_username)
                except PasswordDeleteError:
                    lerror('%s error -> saved_credentials -> not_deleted', __fn_name__)
        if v_login_result == EResult.OK:
            self._login_username = v_prompt_username
            self._login_password = v_prompt_password
            self._login_steamid = self._instance.steam_id
        return v_login_result

    def _login(self, skip_anonymous: bool=False) -> bool:
        __fn_name__ = self._get_fn_name('_login')
        if skip_anonymous and self._login_anonymous:
            linfo('%s skip -> user_is_anonymous', __fn_name__)
            return False
        if self._instance.connected:
            linfo('%s skip -> user_is_already_connected', __fn_name__)
            return True
        if self._login_attempt:
            linfo('%s skip -> user_login_already_attempted', __fn_name__)
            return False
        v_login_result = self._user_login() if not self._login_anonymous else self._instance.anonymous_login()
        if v_login_result == EResult.OK:
            linfo('%s login -> success (anonymous -> %s)', __fn_name__, self._login_anonymous)
            return True
        self._login_attempt = True
        lerror('%s error -> login', __fn_name__)
        return False

    def disconnect(self) -> bool:
        __fn_name__ = self._get_fn_name('disconnect')
        if self._instance.connected:
            self._instance.logout()
            self._instance.disconnect()
            linfo('%s logout -> success', __fn_name__)
            return True
        linfo('%s logout -> already_disconnected', __fn_name__)
        return False

    def get_ugc_info(self, a_id: int) -> Optional[Any]:
        __fn_name__ = self._get_fn_name('get_ugc_info')
        linfo('%s -> %s', __fn_name__, a_id)
        if self._login(True):
            v_request_um = self._instance.send_um_and_wait('PublishedFile.GetDetails#1', params={'publishedfileids': [a_id]}, timeout=APP_REQUESTS_TIMEOUT, raises=False)
            if v_request_um is not None and v_request_um.header.eresult == EResult.OK:
                v_request_um_file_details = v_request_um.body.publishedfiledetails[0]
                if v_request_um_file_details is not None and v_request_um_file_details.result == EResult.OK:
                    return v_request_um_file_details

    def get_ugc_content(self, a_id: int) -> Optional[str]:
        __fn_name__ = self._get_fn_name('get_ugc_content')
        linfo('%s -> %s', __fn_name__, a_id)
        request_um_ugc_info = self.get_ugc_info(a_id)
        if request_um_ugc_info is not None and request_um_ugc_info.file_url is not None:
            request_http_ugc_file = self._request_get(request_um_ugc_info.file_url, a_timeout=False)
            if request_http_ugc_file.status_code == 200:
                return request_http_ugc_file.text
        return None

    def get_inventory_digest(self, a_appid: int) -> Optional[str]:
        __fn_name__ = self._get_fn_name('get_inventory_digest')
        linfo('%s -> %s', __fn_name__, a_appid)
        if self._login(True):
            v_request_um = self._instance.send_um_and_wait('Inventory.GetItemDefMeta#1', params={'appid': a_appid}, timeout=APP_REQUESTS_TIMEOUT, raises=False)
            if v_request_um is not None and v_request_um.header.eresult == EResult.OK:
                return v_request_um.body.digest
        return None

    def get_inventory_info(self, a_appid: int) -> Optional[List[Any]]:
        __fn_name__ = self._get_fn_name('get_inventory_info')
        linfo('%s -> %s', __fn_name__, a_appid)
        v_request_um_digest = self.get_inventory_digest(a_appid)
        if v_request_um_digest is not None:
            v_request_http_items = self._request_get_steam('IGameInventory.GetItemDefArchive', 1, {'appid': a_appid, 'digest': v_request_um_digest})
            if v_request_http_items.status_code == 200:
                return json_loads(v_request_http_items.text[:-1])
        return None

    def get_user_game_stats(self, a_appid: int, a_steamid: int) -> Optional[Dict[str, Any]]:
        __fn_name__ = self._get_fn_name('get_user_game_stats')
        linfo('%s -> %s (%s)', __fn_name__, a_steamid, a_appid)
        if self._login(True):
            v_request_um = self._instance.send_message_and_wait(MsgProto(EMsg.ClientGetUserStats), EMsg.ClientGetUserStatsResponse, body_params={'game_id': a_appid, 'steam_id_for_user': a_steamid, 'crc_stats': 0, 'schema_local_version': -1}, timeout=APP_REQUESTS_TIMEOUT, raises=False)
            if v_request_um is not None and v_request_um.eresult == EResult.OK:
                v_request_um_schema = vdf_binary_loads(v_request_um.schema)
                return v_request_um_schema[str(a_appid)]

    def get_products_info(self, a_appids: List[int], a_timeout=APP_REQUESTS_TIMEOUT) -> Optional[Dict[str, Any]]:
        __fn_name__ = self._get_fn_name('get_products_info')
        linfo('%s -> %s', __fn_name__, a_appids)
        if self._login():
            try:
                v_request_um = self._instance.get_product_info(a_appids, timeout=a_timeout)
                if v_request_um is not None and 'apps' in v_request_um:
                    return v_request_um['apps']
            except Timeout:
                lerror('%s error -> timeout', __fn_name__)
                return
        return None

    def get_product_info(self, a_appid: int) -> Optional[Dict[str, Any]]:
        __fn_name__ = self._get_fn_name('get_product_info')
        linfo('%s -> %s', __fn_name__, a_appid)
        v_request_um = self.get_products_info([a_appid])
        if v_request_um is not None and a_appid in v_request_um:
            return v_request_um[a_appid]
        return None

    def get_changes_since(self, a_since_change_number: int) -> Any:
        __fn_name__ = self._get_fn_name('get_changes_since')
        linfo('%s -> %s', __fn_name__, a_since_change_number)
        if self._login():
            return self._instance.get_changes_since(a_since_change_number)

    def get_app_list(self) -> List[int]:
        v_request_http = self._request_get_steam('ISteamApps.GetAppList', 2)
        v_request_http_out = []
        if v_request_http.status_code == 200:
            v_request_http_json = v_request_http.json()
            if 'applist' in v_request_http_json and 'apps' in v_request_http_json['applist']:
                v_request_http_out = [int(app['appid']) for app in v_request_http_json['applist']['apps']]
        return v_request_http_out