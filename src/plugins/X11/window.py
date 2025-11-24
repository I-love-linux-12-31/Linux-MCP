from typing import Any, Dict, List, Optional
from Xlib import X, Xatom


from src.modules.windows_and_desktop.window import BaseWindow

class X11Window(BaseWindow):
    def __init__(self, wid, priority, display, root):
        self.id = wid
        self.priority = priority

        self.x11_disp = display
        self.x11_root = root

        self.x11_win = None
        self.update_windows_obj()

    def update_windows_obj(self):
        self.x11_win = self.x11_disp.create_resource_object('window', self.id)

    def get_title(self) -> Optional[str]:
        try:
            atom_utf8 = self.x11_disp.intern_atom('UTF8_STRING')
            atom_name = self.x11_disp.intern_atom('_NET_WM_NAME')
            prop = self.x11_win.get_full_property(atom_name, atom_utf8)
            if prop and prop.value:
                if isinstance(prop.value, bytes):
                    return prop.value.decode('utf-8', errors='ignore')
                return str(prop.value)
        except Exception:
            pass
        try:
            prop2 = self.x11_win.get_full_property(self.x11_disp.intern_atom('WM_NAME'), X.AnyPropertyType)
            if prop2 and prop2.value:
                if isinstance(prop2.value, bytes):
                    return prop2.value.decode('utf-8', errors='ignore')
                return str(prop2.value)
        except Exception:
            pass
        return None

    def get_classes(self) -> list:
        try:
            return list(self.x11_win.get_wm_class())
        except Exception:
            return []

    def get_pid(self) -> Optional[int]:
        try:
            pid_prop = self.x11_win.get_full_property(self.x11_disp.intern_atom('_NET_WM_PID'), Xatom.CARDINAL)
            if pid_prop and pid_prop.value:
                try:
                    return int(pid_prop.value[0])
                except Exception:
                    return int(pid_prop.value)
        except Exception:
            pass
        return None

    def get_flags(self) -> List[str]:
        flags = []
        try:
            state_atom = self.x11_disp.intern_atom('_NET_WM_STATE')
            prop = self.x11_win.get_full_property(state_atom, Xatom.ATOM)
            if prop and prop.value:
                for atom in prop.value:
                    try:
                        flags.append(self.x11_disp.get_atom_name(int(atom)))
                    except Exception:
                        pass
        except Exception:
            pass
        return flags

    def get_geometry(self) -> Dict[str, Optional[int]]:
        geom = {'x': None, 'y': None, 'width': None, 'height': None}
        try:
            g = self.x11_win.get_geometry()
            geom['width'] = int(g.width)
            geom['height'] = int(g.height)
        except Exception:
            pass
        try:
            coords = self.x11_win.translate_coords(self.root, 0, 0)
            geom['x'] = int(coords.x)
            geom['y'] = int(coords.y)
        except Exception:
            try:
                g = self.x11_win.get_geometry()
                geom['x'] = int(g.x)
                geom['y'] = int(g.y)
            except Exception:
                pass
        return geom

    def get_geometry_str(self):
        geom = self.get_geometry()
        return f"{geom['x']}x{geom['y']}+{-1 * geom['width']},{-1 * geom['height']}"
