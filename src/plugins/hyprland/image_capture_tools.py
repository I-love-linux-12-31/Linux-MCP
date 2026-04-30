import io
import os
import subprocess
import tempfile
from typing import Optional, Tuple

from PIL import Image as PILImage
from PIL.Image import LANCZOS, MEDIANCUT
from mcp.types import ImageContent, TextContent
from mcp.server.fastmcp import Image as MCPImage

from .hyprland import HyprlandDesktop, get_cursor_position

from src.modules.init_system import get_mcp

mcp = get_mcp()


def _grim_capture(geometry: Optional[str] = None) -> bytes:
    """Capture screen using `grim`. If geometry is given (format 'X,Y WxH'),
    only that region is captured; otherwise the full output area."""
    cmd = ["grim"]
    if geometry:
        cmd += ["-g", geometry]
    cmd += ["-"]
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except FileNotFoundError:
        raise RuntimeError(
            "grim not found. Install grim (Wayland screenshot tool) to capture screens under Hyprland."
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
        raise RuntimeError(f"grim failed: {stderr or e}")
    return result.stdout


def _paste_cursor(image: PILImage.Image) -> PILImage.Image:
    """Overlay the project's cursor PNG at the actual cursor position (Wayland-safe)."""
    pos = get_cursor_position()
    if not pos:
        return image
    cursor_path = "resources/cursor.png"
    if not os.path.exists(cursor_path):
        return image
    try:
        cursor = PILImage.open(cursor_path)
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        image.paste(cursor, (pos["x"], pos["y"]), cursor)
    except Exception:
        # Cursor overlay is best-effort; never fail the screenshot for it.
        pass
    return image


@mcp.tool(name="Window-Get-Image")
def get_window_image(window_hex_id: str) -> list:
    """
    Returns screenshot of a single window by hex address (e.g. 0x55a8f0c8a0e0) and its metadata.
    Hyprland implementation uses grim to capture the window's reported geometry.
    Keywords: Hyprland, Wayland, window, image, GUI, image_grab, window_manager, Linux-MCP
    """
    desktop = HyprlandDesktop()
    window = desktop[window_hex_id]
    geom = window.get_geometry()
    if None in (geom["x"], geom["y"], geom["width"], geom["height"]):
        raise RuntimeError(f"Window {window_hex_id} has no resolvable geometry.")

    geometry_str = f"{geom['x']},{geom['y']} {geom['width']}x{geom['height']}"
    img_bytes = _grim_capture(geometry_str)

    metadata_text = (
        f"address: {window.address}\n"
        f"title: {window.get_title()}\n"
        f"classes: {window.get_classes()}\n"
        f"position: ({geom['x']}, {geom['y']})\n"
        f"size: {geom['width']}x{geom['height']}\n"
        f"flags: {window.get_flags()}"
    )
    metadata = TextContent(type="text", text=metadata_text)
    img_obj = MCPImage(data=img_bytes, format="png")
    return [img_obj.to_image_content(), metadata]


@mcp.tool(name="Desktop-Get-Image")
def get_full_desktop() -> ImageContent:
    """
    Returns high quality image of the full desktop (all monitors). Uses grim. If file is too large use Desktop-Get-Image-Compressed tool.
    Keywords: Hyprland, Wayland, window, image, GUI, image_grab, desktop, screenshot, Linux-MCP
    """
    img_bytes = _grim_capture()
    image = PILImage.open(io.BytesIO(img_bytes))
    image = _paste_cursor(image)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_obj = MCPImage(data=buffer.getvalue(), format="png")
    return img_obj.to_image_content()


@mcp.tool(name="Desktop-Get-Image-Compressed")
def get_full_desktop_compressed(
    max_width: int = 1920,
    max_height: int = 1200,
    quality: int = 75,
    reduce_colors: bool = False,
) -> list:
    """
    Returns compressed image of the full desktop with smart optimization and metadata.

    Args:
        max_width: Maximum width (default 1920)
        max_height: Maximum height (default 1200)
        quality: JPEG quality 1-95 (default 75)
        reduce_colors: Apply color quantization (default False)

    Keywords: Hyprland, Wayland, window, image, GUI, image_grab, desktop, screenshot, Linux-MCP
    """
    img_bytes = _grim_capture()
    image = PILImage.open(io.BytesIO(img_bytes))
    image = _paste_cursor(image)

    original_size = image.size
    pre_buffer = io.BytesIO()
    image.save(pre_buffer, format="PNG")
    original_format_size = len(pre_buffer.getvalue())
    del pre_buffer

    width, height = image.size
    aspect_ratio = width / height if height else 1.0

    if width > max_width or height > max_height:
        if width / max_width > height / max_height:
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(max_height * aspect_ratio)
        image = image.resize((new_width, new_height), LANCZOS)

    if reduce_colors:
        if image.mode in ("RGBA", "LA", "P"):
            background = PILImage.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(
                image,
                mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None,
            )
            image = background
        image = image.quantize(colors=256, method=MEDIANCUT).convert("RGB")
    elif image.mode == "RGBA":
        image = image.convert("RGB")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    final_bytes = buffer.getvalue()

    img_obj = MCPImage(data=final_bytes, format="jpeg")
    compression_ratio = (1 - len(final_bytes) / original_format_size) * 100 if original_format_size else 0.0
    metadata = TextContent(
        type="text",
        text=(
            f"Screenshot captured and compressed:\n"
            f"Original: {original_size[0]}x{original_size[1]}\n"
            f"Compressed: {image.size[0]}x{image.size[1]}\n"
            f"Size: ~{len(final_bytes) / 1024:.1f} KB\n"
            f"Compression: {compression_ratio:.1f}% reduction\n"
            f"Quality: {quality}, Colors: {'reduced' if reduce_colors else 'full'}"
        ),
    )
    return [img_obj.to_image_content(), metadata]
