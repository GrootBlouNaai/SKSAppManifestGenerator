from typing import Tuple
from src.sks_retriever.sk_types import TYPE_ACH_IMAGES_DATA, TYPE_ACHS_DATA, TYPE_STATS_DATA, TYPE_STATS_INFO
_ACH_STAT_TYPE_INT = '1'
_ACH_STAT_TYPE_FLOAT = '2'
_ACH_STAT_TYPE_AVGRATE = '3'
_ACH_STAT_TYPE_BITS = '4'

def h_parser_stats(a_appid: str, a_appid_stats_info: TYPE_STATS_INFO, a_ach_imgs_retrieve: bool) -> Tuple[(TYPE_ACHS_DATA, TYPE_ACH_IMAGES_DATA, TYPE_STATS_DATA)]:
    v_achs_out = []
    v_ach_imgs_out = []
    v_stats_out = []
    v_ach_icon_preurl = f"https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/{a_appid}"
    if 'stats' in a_appid_stats_info:
        v_stats_info = a_appid_stats_info['stats']
        for _v_stats_info_key, v_stat_info in v_stats_info.items():
            v_stat_info_type = v_stat_info['type']
            if v_stat_info_type == _ACH_STAT_TYPE_BITS:
                v_stat_info_bits = v_stat_info['bits']
                for _v_stat_info_bit_key, v_stat_info_bit_info in v_stat_info_bits.items():
                    v_stat_info_bit_display = v_stat_info_bit_info['display']
                    v_ach_name = v_stat_info_bit_info['name']
                    v_ach_display_name = v_stat_info_bit_display['name']
                    v_ach_display_desc = v_stat_info_bit_display['desc']
                    v_ach_hidden = int(v_stat_info_bit_display.get('hidden', 0))
                    v_ach_out = {'name':v_ach_name, 
                     'displayName':v_ach_display_name, 
                     'description':v_ach_display_desc, 
                     'hidden':v_ach_hidden}
                    if 'icon' in v_stat_info_bit_display:
                        v_ach_icon_fname = v_stat_info_bit_display['icon']
                        v_ach_icon_url = f"{v_ach_icon_preurl}/{v_ach_icon_fname}"
                        v_ach_out['icon'] = v_ach_icon_fname if a_ach_imgs_retrieve else v_ach_icon_url
                        v_ach_imgs_out.append(v_ach_icon_url)
                    if 'icon_gray' in v_stat_info_bit_display:
                        v_ach_icon_gray_fname = v_stat_info_bit_display['icon_gray']
                        v_ach_icon_gray_url = f"{v_ach_icon_preurl}/{v_ach_icon_gray_fname}"
                        v_ach_out['icon_gray'] = v_ach_icon_gray_fname if a_ach_imgs_retrieve else v_ach_icon_gray_url
                        v_ach_imgs_out.append(v_ach_icon_gray_url)
                    if 'progress' in v_stat_info_bit_info:
                        v_ach_out['progress'] = v_stat_info_bit_info['progress']
                    v_achs_out.append(v_ach_out)

            else:
                v_stat_info_name = v_stat_info['name']
                v_stat_display_name = '_missing_'
                if 'display' in v_stat_info:
                    if 'name' in v_stat_info['display']:
                        v_stat_display_name = v_stat_info['display']['name']
                v_stat_type = '_missing_'
                if v_stat_info_type == _ACH_STAT_TYPE_INT:
                    v_stat_type = 'int'
                else:
                    if v_stat_info_type == _ACH_STAT_TYPE_FLOAT:
                        v_stat_type = 'float'
                    else:
                        if v_stat_info_type == _ACH_STAT_TYPE_AVGRATE:
                            v_stat_type = 'avgrate'
                        else:
                            v_stat_incrementonly = 'incrementonly' in v_stat_info
                            v_stat_default = None
                            if 'default' in v_stat_info:
                                v_stat_info_default = v_stat_info['default']
                                if v_stat_type == 'int':
                                    try:
                                        v_stat_default = int(v_stat_info_default)
                                    except ValueError:
                                        v_stat_default = int(float(v_stat_info_default))

                                else:
                                    v_stat_default = float(v_stat_info_default)
                            else:
                                v_stat_default = 0 if v_stat_type == 'int' else 0.0
                v_stats_out.append({'name':v_stat_info_name, 
                 'displayName':v_stat_display_name, 
                 'type':v_stat_type, 
                 'incrementonly':v_stat_incrementonly, 
                 'default':v_stat_default})

    return (v_achs_out, v_ach_imgs_out, v_stats_out)