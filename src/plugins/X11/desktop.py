from typing import Any, Dict, List, Optional
import os
import sys
import traceback
import subprocess
import re
from Xlib import display, X, Xatom, error
from Xlib.ext import randr


from src.modules.windows_and_desktop.desktop import BaseDesktopInfo
from .helpers import get_window_list_by_property
from .window import X11Window


class X11Desktop(BaseDesktopInfo):
    def __init__(self, display_name: Optional[str] = None):
        try:
            self.x11_disp = display.Display(display_name) if display_name else display.Display()
            self.x11_root = self.x11_disp.screen().root
        except Exception as e:
            raise RuntimeError(f"Unable to open X display (is DISPLAY set and X11 running?): {e}")

        self.displays = []
        self.windows = []

        self.update_state()

    def __getitem__(self, item) -> X11Window:
        return super().__getitem__(item)

    def update_displays_info(self):
        #  randr.get_output_info has problem with display name reading(incorrect memory read, without SIGSEGV). CLI interface will be used instead it.
        try:
            out = subprocess.check_output(['xrandr', '--listmonitors'], stderr=subprocess.STDOUT)
            lines = out.decode(errors='ignore').splitlines()
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise RuntimeError("Failed to call xrandr(Not found)!")

        displays = []
        # regex to find geometry token like 1920/344x1080/194+0+0 or 1920x1080+0+0
        geom_re = re.compile(r'(\d+)(?:/\d+)?x(\d+)(?:/\d+)?\+(-?\d+)\+(-?\d+)')
        for line in lines[1:]:  # skip header line 'Monitors: N'
            parts = line.strip().split()
            name = parts[-1] if parts else None
            geom = None
            for token in parts:
                m = geom_re.search(token)
                if m:
                    geom = m
                    break
            if geom:
                w = int(geom.group(1))
                h = int(geom.group(2))
                x = int(geom.group(3))
                y = int(geom.group(4))
                displays.append({'name': name, 'width': w, 'height': h, 'x': x, 'y': y})
            else:
                # fallback token style 1920x1080+0+0
                for token in parts:
                    m = re.search(r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)', token)
                    if m:
                        w = int(m.group(1))
                        h = int(m.group(2))
                        x = int(m.group(3))
                        y = int(m.group(4))
                        displays.append({'name': name, 'width': w, 'height': h, 'x': x, 'y': y})
                        break
        self.displays.clear()
        self.displays = displays


    def load_windows(self):
        self.windows.clear()
        windows_list = get_window_list_by_property(
            self.x11_disp,
            self.x11_root,
            "_NET_CLIENT_LIST_STACKING")

        self.windows.clear()
        self.windows = [X11Window(wid, i, self.x11_disp, self.x11_root) for i, wid in enumerate(windows_list[::-1])]


if __name__ == '__main__':
    __desktop = X11Desktop()
    # print(__desktop.displays)
    # for win in __desktop.windows:
    #     print(win.serialize())
    print(__desktop.serialize())

