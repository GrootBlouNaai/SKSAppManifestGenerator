from logging import error as lerror
from logging import info as linfo
from logging import warning as lwarn
from os import environ
from pathlib import Path
from threading import current_thread, main_thread
from tkinter import Tk
from tkinter.messagebox import askyesno, showerror, showinfo, showwarning
from tkinter.simpledialog import askstring
from typing import Optional, Tuple
from pwinput import pwinput
_SKGUI_MASTER_WINDOW = Tk()
_SKGUI_MASTER_WINDOW.withdraw()
_SKGUI_MASTER_WINDOW.attributes('-topmost', True)
_SKGUI_MASTER_WINDOW_TITLE = None
_SKGUI_MASTER_WINDOW_TITLE: Optional[str]
_SKGUI_MASTER_WINDOW_ICON = None
_SKGUI_MASTER_WINDOW_ICON: Optional[Path]

class SKGuiMaster:

    @staticmethod
    def title(a_title: str) -> None:
        _SKGUI_MASTER_WINDOW.title(a_title)
        _SKGUI_MASTER_WINDOW_TITLE = a_title

    @staticmethod
    def icon(a_icon: Path) -> None:
        _SKGUI_MASTER_WINDOW.iconbitmap(bitmap=a_icon, default=a_icon)
        _SKGUI_MASTER_WINDOW_ICON = a_icon

    @staticmethod
    def get_screen_width() -> int:
        v_parent, v_parent_is_main_thread = SKGuiMaster._get_master_window()
        v_value = v_parent.winfo_screenwidth()
        if not v_parent_is_main_thread:
            v_parent.destroy()
        return v_value

    @staticmethod
    def get_screen_height() -> int:
        v_parent, v_parent_is_main_thread = SKGuiMaster._get_master_window()
        v_value = v_parent.winfo_screenheight()
        if not v_parent_is_main_thread:
            v_parent.destroy()
        return v_value

    @staticmethod
    def _get_master_window() -> Tuple[(Tk, bool)]:
        if current_thread() is main_thread():
            return (
             _SKGUI_MASTER_WINDOW, True)
        v_wtmp = Tk()
        v_wtmp.withdraw()
        v_wtmp.attributes('-topmost', True)
        if _SKGUI_MASTER_WINDOW_TITLE is not None:
            v_wtmp.title(_SKGUI_MASTER_WINDOW_TITLE)
        if _SKGUI_MASTER_WINDOW_ICON is not None:
            v_wtmp.iconbitmap(bitmap=_SKGUI_MASTER_WINDOW_ICON, default=_SKGUI_MASTER_WINDOW_ICON)
        return (
         v_wtmp, False)

    @staticmethod
    def _show_window_enabled() -> bool:
        return environ.get('SK_SHOW_WINDOW', '0') == '1'

    @staticmethod
    def _askstring_cli(a_title: str, a_message: str, a_hide: bool=False) -> str:
        v_prompt = f"({a_title}) {a_message} "
        v_reply = pwinput(v_prompt) if a_hide else input(v_prompt)
        return v_reply

    @staticmethod
    def askstring(a_title: str, a_message: str, a_hide: bool=False) -> str:
        if SKGuiMaster._show_window_enabled():
            v_parent, v_parent_is_main_thread = SKGuiMaster._get_master_window()
            v_raw = askstring(a_title, a_message, show='*', parent=v_parent) if a_hide else askstring(a_title, a_message, parent=v_parent)
            if not v_parent_is_main_thread:
                v_parent.destroy()
            if v_raw is not None:
                return v_raw
            return ''
        return SKGuiMaster._askstring_cli(a_title, a_message, a_hide)

    @staticmethod
    def showerror(a_title: str, a_message: str) -> None:
        lerror(a_message)
        if SKGuiMaster._show_window_enabled():
            v_parent, v_parent_is_main_thread = SKGuiMaster._get_master_window()
            showerror(a_title, a_message, parent=v_parent)
            if not v_parent_is_main_thread:
                v_parent.destroy()

    @staticmethod
    def showinfo(a_title: str, a_message: str) -> None:
        linfo(a_message)
        if SKGuiMaster._show_window_enabled():
            v_parent, v_parent_is_main_thread = SKGuiMaster._get_master_window()
            showinfo(a_title, a_message, parent=v_parent)
            if not v_parent_is_main_thread:
                v_parent.destroy()

    @staticmethod
    def showwarning(a_title: str, a_message: str) -> None:
        lwarn(a_message)
        if SKGuiMaster._show_window_enabled():
            v_parent, v_parent_is_main_thread = SKGuiMaster._get_master_window()
            showwarning(a_title, a_message, parent=v_parent)
            if not v_parent_is_main_thread:
                v_parent.destroy()

    @staticmethod
    def askyesno(a_title: str, a_message: str) -> bool:
        if SKGuiMaster._show_window_enabled():
            v_parent, v_parent_is_main_thread = SKGuiMaster._get_master_window()
            v_reply = askyesno(a_title, a_message, parent=v_parent)
            if not v_parent_is_main_thread:
                v_parent.destroy()
        else:
            return v_reply
            v_reply = None
            while True:
                if v_reply not in ('y', 'n'):
                    v_reply = input(f"({a_title}) {a_message} (y/n): ").casefold()

        return v_reply == 'y'