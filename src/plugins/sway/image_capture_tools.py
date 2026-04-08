import io
import pyautogui

from PIL.Image import Image, LANCZOS, MEDIANCUT, open as open_image
from mcp.types import ImageContent, TextContent
from mcp.server.fastmcp import Image as MCPImage


from src.modules.init_system import get_mcp

mcp = get_mcp()


@mcp.tool(name="Desktop-Get-Image")
def get_full_desktop() -> ImageContent:
    """
    Returns high quality image of full-screen. If file is too large use Desktop-Get-Image-Compressed tool.
    Keywords: X11, window, image, GUI, image_grab, desktop, screenshot, Linux-MCP
    """
    buffer = io.BytesIO()
    image = pyautogui.screenshot()

    cursor_x, cursor_y = pyautogui.position()
    cursor: Image = open_image("resources/cursor.png")
    cursor_x, cursor_y = pyautogui.position()
    image.paste(cursor, (cursor_x, cursor_y), cursor)

    image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_obj = MCPImage(data=img_bytes, format="png")

    return img_obj.to_image_content()


@mcp.tool(name="Desktop-Get-Image-Compressed")
def get_full_desktop_compressed(
        max_width: int = 1920,
        max_height: int = 1200,
        quality: int = 75,
        reduce_colors: bool = False
) -> list[ImageContent | TextContent]:
    """
    Returns compressed image of full-screen with smart optimization and some metadata.

    Args:
        max_width: Maximum width (default 1920)
        max_height: Maximum height (default 1200)
        quality: JPEG quality 1-95 (default 75)
        reduce_colors: Apply color quantization (default False)
    Keywords: X11, window, image, GUI, image_grab, desktop, screenshot, Linux-MCP
    """
    image = pyautogui.screenshot()

    cursor_x, cursor_y = pyautogui.position()
    cursor: Image = open_image("resources/cursor.png")
    cursor_x, cursor_y = pyautogui.position()
    image.paste(cursor, (cursor_x, cursor_y), cursor)
    # todo: make HD cursor

    original_size = image.size

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    original_format_size = len(buffer.getvalue())
    del buffer

    # Calculate new dimensions while maintaining aspect ratio
    width, height = image.size
    aspect_ratio = width / height

    if width > max_width or height > max_height:
        if width / max_width > height / max_height:
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(max_height * aspect_ratio)

        # High-quality resize with LANCZOS resampling
        image = image.resize((new_width, new_height), LANCZOS)

    # Optional: Reduce color palette for further compression
    if reduce_colors:
        # Convert to RGB if needed
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparency
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background

        # Quantize to reduce colors (adaptive palette)
        image = image.quantize(colors=256, method=MEDIANCUT).convert('RGB')

    # Save as JPEG with optimized quality
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    img_bytes = buffer.getvalue()

    # Create image content
    img_obj = MCPImage(data=img_bytes, format="jpeg")

    # Create metadata text
    compression_ratio = (1 - len(img_bytes) / original_format_size) * 100
    metadata = TextContent(
        type="text",
        text=f"Screenshot captured and compressed:\n"
             f"Original: {original_size[0]}x{original_size[1]}\n"
             f"Compressed: {image.size[0]}x{image.size[1]}\n"
             f"Size: ~{len(img_bytes) / 1024:.1f} KB\n"
             f"Compression: {compression_ratio:.1f}% reduction\n"
             f"Quality: {quality}, Colors: {'reduced' if reduce_colors else 'full'}"
    )

    return [img_obj.to_image_content(), metadata]
