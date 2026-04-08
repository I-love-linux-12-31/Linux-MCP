import io
import copykitten
from PIL import Image
import mss

import pyautogui

from mcp.types import ImageContent
from mcp.server.fastmcp import Image as MCPImage

from src.modules.init_system import get_mcp

mcp = get_mcp()

@mcp.tool(name="Clipboard-Get-Text")
async def get_text() -> str:
    """
    Returns text from clipboard.
    Keywords: clipboard, copy, paste, clipboard_get, Linux-MCP
    """
    return copykitten.paste()


@mcp.tool(name="Clipboard-Set-Text")
async def set_text(text: str) -> None:
    """
    Writes text to clipboard.
    Keywords: clipboard, copy, clipboard_set, Linux-MCP
    """
    return copykitten.copy(text)

@mcp.tool(name="Clipboard-Get-Image")
async def get_image() -> ImageContent:
    """
    Returns image from clipboard.
    Keywords: clipboard, copy, paste, image, clipboard_get, Linux-MCP
    """
    pixels, width, height = copykitten.paste_image()
    image = Image.frombytes(mode="RGBA", size=(width, height), data=pixels)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_obj = MCPImage(data=img_bytes, format="png")
    return img_obj.to_image_content()


@mcp.tool(name="Clipboard-Copy-Image")
async def copy_image(x: int, y: int, width: int, height: int) -> None:
    """
    Copies screen area to clipboard.
    Keywords: clipboard, copy, clipboard_set, image, screenshot, Linux-MCP
    """
    with mss.mss() as sct:
        area = {"top": y, "left": x, "width": width, "height": height}
        screenshot = sct.grab(area)
        img = Image.new("RGBA", screenshot.size)
        pixels = zip(
            screenshot.raw[2::4],
            screenshot.raw[1::4],
            screenshot.raw[::4],
            [255] * screenshot.width * screenshot.height
        )
        img.putdata(list(pixels))

    copykitten.copy_image(img.tobytes("raw", "RGBA"), img.width, img.height)


@mcp.tool(name="Clipboard-Paste-CtrlV")
async def paste(x: int, y: int, click: bool = True) -> None:
    """
    Pastes clipboard using Ctrl + V.
    x and y are coordinates. click is boolean flag, that requests click before paste.
    Keywords: clipboard, paste, hotkey, Linux-MCP
    """
    if click:
        pyautogui.click(x, y)
    pyautogui.hotkey("ctrl", "v")

@mcp.tool(name="Clipboard-Paste-CtrlShiftV")
async def paste_alt(x: int, y: int, click: bool = True) -> None:
    """
    Pastes clipboard using Ctrl + Shift + V. Useful for most terminal apps.
    x and y are coordinates. click is boolean flag, that requests click before paste.
    Keywords: clipboard, paste, hotkey, Linux-MCP
    """
    if click:
        pyautogui.click(x, y)
    pyautogui.hotkey("ctrl", "shift", "v")
