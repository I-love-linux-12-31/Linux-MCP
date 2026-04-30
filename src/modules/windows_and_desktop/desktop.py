import os


from .window import BaseWindow


class BaseDesktopInfo:
    is_X11: bool
    is_Wayland: bool
    desktop_environment: str

    default_display: int
    displays: list[dict]

    windows: list[BaseWindow]

    def update_state(self):
        self.find_session_info()
        self.update_displays_info()

        self.load_windows()


    def update_displays_info(self):
        raise NotImplementedError()

    def __getitem__(self, item: int | str) -> BaseWindow:
        if isinstance(item, str):
            item = int(item, 16)
        for window in self.windows:
            if window.id == item:
                return window
        raise KeyError(F"No window with id: {item}")

    def find_session_info(self):
        de = "unknown"
        for v in ('XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION', 'GDMSESSION'):
            if os.environ.get(v):
                de = os.environ.get(v)
        session = os.environ.get("XDG_SESSION_TYPE", "?")

        if de.lower() == "hyprland":
            session = "wayland"

        if session.lower() == "x11":
            self.is_X11 = True
            self.is_Wayland = False
        elif session.lower() == "wayland":
            self.is_X11 = False
            self.is_Wayland = True
        else:
            # No data!
            self.is_X11 = False
            self.is_Wayland = False
        self.desktop_environment = de

    def load_windows(self):
        raise NotImplementedError()

    def serialize(self):
        if self.is_X11:
            focused = hex([win for win in self.windows if "_NET_WM_STATE_FOCUSED" in win.get_flags()][0].id)
        else:
            focused = "Unknown"
        return {
            "session_info": {
                "X11 display": self.is_X11,
                "Wayland": self.is_Wayland,
                "Desktop environment": self.desktop_environment,
                "default_display": "unknown",# self.default_display,
                "Displays":
                [
                    {
                        "name": disp["name"],
                        "size": [disp["width"], disp["height"]],
                        "position": [disp["x"], disp["y"]]
                    }
                    for disp in self.displays
                ]
            },
            "windows_data": {
                "active_window_id": focused,
                "windows_top_to_bottom_order": [
                    win.serialize() for win in self.windows
                ]
            }
        }
