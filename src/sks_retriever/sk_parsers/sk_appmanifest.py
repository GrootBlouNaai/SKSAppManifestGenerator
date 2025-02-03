from logging import info as linfo
from typing import Optional
from steam.steamid import SteamID
from src.sk_common.sk_utilities.sk_is_empty import h_is_empty
from src.sks_retriever.sk_types import TYPE_APPMANIFEST_OUT_DATA, TYPE_INFO_OUT_DATA

def h_parser_appmanifest(self, a_appid_info_out: TYPE_INFO_OUT_DATA, a_last_owner: Optional[SteamID]=None) -> TYPE_APPMANIFEST_OUT_DATA:
    __fn_name__ = self.get_fn_name('h_parser_appmanifest')
    v_appid = a_appid_info_out['AppId']
    v_name = a_appid_info_out['Name']
    v_last_owner = a_last_owner
    v_installdir = a_appid_info_out['InstallDir']
    v_buildid = str(a_appid_info_out['BuildId'])
    v_size = 0
    v_depots = a_appid_info_out['Depots']
    for _v_depot_id, v_depot_info in h_is_empty(v_depots) or v_depots.items():
        v_size += v_depot_info['size']
    else:
        v_depots_shared = a_appid_info_out['DepotsShared']
        linfo('%s last_owner -> %s', __fn_name__, a_last_owner)
        linfo('%s size -> %s', __fn_name__, v_size)
        v_appmanifest_out = {'AppState': {'appid':v_appid, 
                      'Universe':1, 
                      'LauncherPath':'', 
                      'name':v_name, 
                      'StateFlags':4, 
                      'installdir':v_installdir, 
                      'LastUpdated':0, 
                      'SizeOnDisk':v_size, 
                      'StagingSize':0, 
                      'buildid':v_buildid, 
                      'LastOwner':v_last_owner, 
                      'UpdateResult':0, 
                      'BytesToDownload':0, 
                      'BytesDownloaded':0, 
                      'BytesToStage':0, 
                      'BytesStaged':0, 
                      'TargetBuildID':0, 
                      'AutoUpdateBehavior':0, 
                      'AllowOtherDownloadsWhileRunning':0, 
                      'ScheduledAutoUpdate':0}}
        if not h_is_empty(v_depots):
            v_appmanifest_out['AppState']['InstalledDepots'] = v_depots
        if not h_is_empty(v_depots_shared):
            v_appmanifest_out['AppState']['SharedDepots'] = v_depots_shared
        return v_appmanifest_out