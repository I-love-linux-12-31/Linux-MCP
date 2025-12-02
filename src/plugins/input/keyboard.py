import pyautogui
from typing import Literal

from src.modules.init_system import get_mcp

mcp = get_mcp()


def _fix_pyautogui_keys(keys: list[str]) -> list[str]:
    """
    Pyautogui can process super key with 'win' name, but not 'super'.
    """
    result = []
    for key in keys:
        if key.lower() == "super":
            result.append("win")
        else:
            result.append(key)
    return result


@mcp.tool(name="Keyboard-Single-Key-Press")
def single_keypress(key: str = "", presses: int = 1):
    """
    Press individual keyboard keys.
    Supports special keys like "enter", "escape", "tab", "space", "backspace", "delete",
    arrow keys ("up", "down", "left", "right"), function keys ("f1"-"f12").
    'presses' argument allows to make multiple presses for one key, defaults = 1.
    """
    pyautogui.press(_fix_pyautogui_keys([key])[0], presses=presses, interval=0.05)


@mcp.tool(name="Keyboard-Hotkey-Press")
def hotkey_press(hotkey:list[str]):
    """
    Press multiple keyboard keys in combinations like ["ctrl", "c"], ["shift", "alt"] or ["alt", "f2"].
    Supports special keys like "enter", "escape", "tab", "space", "backspace", "delete",
    arrow keys ("up", "down", "left", "right"), function keys ("f1"-"f12").
    """
    pyautogui.hotkey(*_fix_pyautogui_keys(hotkey))

@mcp.tool(name="Keyboard-Type-Line-Of-Text")
def type_line_of_text(text: str) -> str:
    """
    Types single line of text.
    """
    warning_chars = []
    for char in text:
        try:
            pyautogui.press(char, interval=0.05)
        except Exception as e:
            print(e)
            warning_chars.append(f"'{char}'")

    if not warning_chars:
        return "Success"
    else:
        return F"Done, but failed to type literals: [{', '.join(warning_chars)}]"


@mcp.tool(name="Keyboard-Type-Text")
def type_text(text: str) -> str:
    """
    Types big text. '\n' character supported.
    """
    warning_chars = []
    for char in text:
        if char == "\n":
            single_keypress("enter")
            continue
        try:
            pyautogui.press(char, interval=0.05)
        except Exception as e:
            print(e)
            warning_chars.append(f"'{char}'")

    if not warning_chars:
        return "Success"
    else:
        return F"Done, but failed to type literals: [{', '.join(warning_chars)}]"
