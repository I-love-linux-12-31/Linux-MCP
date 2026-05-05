import io
from pathlib import Path

from PIL import Image
from mcp.types import ImageContent
from mcp.server.fastmcp import Image as MCPImage

from mcp.server.fastmcp import FastMCP
from src.modules.init_system import get_mcp

mcp: FastMCP = get_mcp()


@mcp.tool(name="File-Read")
def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    Read and return the contents of a file.
    Args:
        path: Absolute or relative path to the file.
        encoding: File encoding. Default = 'utf-8'.
    Returns:
        File contents as a string.
    Keywords: file, read, load, get content, Linux-MCP
    """
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
    return file_path.read_text(encoding=encoding)


@mcp.tool(name="File-Write")
def write_file(path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> str:
    """
    Write content to a file, overwriting it if it already exists.
    Args:
        path: Absolute or relative path to the file.
        content: Text content to write.
        encoding: File encoding. Default = 'utf-8'.
        create_dirs: Automatically create parent directories if they don't exist. Default = True.
    Returns:
        Confirmation message with the resolved file path.
    """
    file_path = Path(path).expanduser().resolve()
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)
    return f"File written successfully: {file_path}"


@mcp.tool(name="File-Update")
def update_file(
    path: str,
    content: str,
    mode: str = "append",
    old_fragment: str = "",
    encoding: str = "utf-8",
) -> str:
    """
    Update an existing file by appending, prepending, or replacing a substring.
    Args:
        path: Absolute or relative path to the file.
        content: Content to add or use as replacement.
        mode: Update mode — one of:
              'append'  : add content at the end of the file (default),
              'prepend' : add content at the beginning of the file,
              'replace' : replace the entire file content (same as File-Write).
        encoding: File encoding. Default = 'utf-8'.
    Returns:
        Confirmation message with the resolved file path.
    Keywords: file, update, edit, Linux-MCP
    """
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if mode == "replace":
        if not old_fragment:
            raise ValueError(
                "'old_fragment' must not be empty when using 'replace' mode. "
                "Provide the exact text to be replaced."
            )
        existing = file_path.read_text(encoding=encoding)
        count = existing.count(old_fragment)
        if count == 0:
            raise ValueError(
                f"Fragment not found in '{file_path}'.\n"
                f"Fragment: {old_fragment!r}"
            )
        if count > 1:
            raise ValueError(
                f"Fragment appears {count} times in '{file_path}' — replacement is ambiguous. "
                "Provide a more specific fragment."
            )
        file_path.write_text(existing.replace(old_fragment, content, 1), encoding=encoding)
    elif mode == "append":
        with file_path.open("a", encoding=encoding) as f:
            f.write(content)
    elif mode == "prepend":
        existing = file_path.read_text(encoding=encoding)
        file_path.write_text(content + existing, encoding=encoding)
    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'append', 'prepend', or 'replace'.")

    return f"File updated ({mode}) successfully: {file_path}"


@mcp.tool(name="File-Read-Image")
def read_image_file(path: str) -> ImageContent:
    """
    Read and return the contents of a file with image.
    Args:
        path: Absolute or relative path to the file.
    Returns:
        File contents as image.
    Keywords: file, image, picture, read, load, Linux-MCP
    """
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    image = Image.open(file_path)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_obj = MCPImage(data=img_bytes, format="png")
    return img_obj.to_image_content()
