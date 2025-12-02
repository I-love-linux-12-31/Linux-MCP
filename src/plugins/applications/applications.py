import os
import pathlib
import sys
import subprocess
from xdg.DesktopEntry import DesktopEntry
import xdg

from mcp.types import ImageContent
from mcp.server.fastmcp import Image as MCPImage

from src.modules.init_system import get_mcp

mcp = get_mcp()



xdg.Locale.update("en_US")

DESKTOP_FOLDERS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    F"/home/{os.environ['USER']}/.local/share/applications"
]


def _get_info_by_file(path: str) -> (str, dict):
    if (not os.path.exists(path)) or os.path.isdir(path):
        raise RuntimeWarning(F"{path} is not readable .desktop file! Ignoring.")
    data = DesktopEntry(filename=path)
    # print(data)
    # print(data.content)
    try:
        return str(data), data.content
    except AttributeError:
        print(F"[\033[31mError\033[0m] Failed to load .desktop file: {path}!")
        raise RuntimeError


def _load_all_desktop_files_info() -> dict:
    paths = []
    for directory_path in DESKTOP_FOLDERS:
        paths += [directory_path + "/" + i for i in os.listdir(directory_path) if os.path.exists(directory_path)]

    data = dict()
    for path in paths:
        try:
            key, value = _get_info_by_file(path)
            data[key] = path
        except RuntimeWarning as w:
            print(F"[\033[33mWarning\033[0m] {w}")
        except RuntimeError:
            pass
        except xdg.Exceptions.ParsingError as e:
            print(F"[\033[33mWarning\033[0m] {e}")
    return data


def _get_applications_list():
    return list(_load_all_desktop_files_info().keys())


def _search_app_by_name(name):
    data = _load_all_desktop_files_info()
    keys = list(filter(lambda i: name.lower() in i.lower(), list(_load_all_desktop_files_info().keys())))
    return {key: data[key] for key in data if key.lower() in keys}


def _get_app_info(name):
    return _get_info_by_file(_load_all_desktop_files_info()[name])


def _start_app_by_name(name):
    path = _load_all_desktop_files_info().get(name, None)
    if path is None:
        raise Exception("Failed to start apop. Unknown name. ")
    try:
        subprocess.Popen(["gio", "launch", path])
    except Exception as e:
        raise Exception(F"Failed to start apop. Error: {e}")

    return "App successfully called."


@mcp.tool(name="Applications-Get-List")
def get_applications_list() -> list[str, ]:
    """
    Returns list of applications with .desktop files.
    """
    return _get_applications_list()


@mcp.tool(name="Applications-Get-Info")
def get_application_info(name: str) -> tuple[str, dict]:
    # todo: Add different modes: 1) by name 2) by path
    """
    Returns information about an application.
    """
    return _get_app_info(name)


@mcp.tool(name="Applications-Start")
def start_application(name) -> str:
    """
    Call application start. Tool doesn't guarantee that application successfully started.
    """
    # todo: Add different modes: 1) by name 2) by path
    return _start_app_by_name(name)
