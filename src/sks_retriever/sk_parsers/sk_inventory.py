from src.sks_retriever.sk_types import TYPE_INV_DATA, TYPE_INV_INFO

def h_parser_inventory(a_inv_info: TYPE_INV_INFO) -> TYPE_INV_DATA:
    v_inv_out = {}
    for v_inv_items in a_inv_info:
        v_inv_item_id = v_inv_items['itemdefid']
        v_inv_item = {v_inv_key: str(v_inv_items[v_inv_key]).lower() if isinstance(v_inv_items[v_inv_key], bool) else str(v_inv_items[v_inv_key]) for v_inv_key in v_inv_items}
        v_inv_out[v_inv_item_id] = v_inv_item
    return v_inv_out