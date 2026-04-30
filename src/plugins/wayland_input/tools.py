from src.modules.windows_and_desktop.desktop import BaseDesktopInfo

__desktop = BaseDesktopInfo()
__desktop.update_state()
if not __desktop.is_X11:
    from .keyboard import (
        single_keypress,
        hotkey_press,
        type_line_of_text,
        type_text
    )
    from .cursor import (
        move,
        click_wa,
        # click,
        # drag_and_drop,
        # get_position,
    )
