from datetime import datetime
import os
import stat
import shutil
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from src.modules.init_system import get_mcp

mcp: FastMCP = get_mcp()


@mcp.tool(name="File-Copy")
def copy_file(source: str, destination: str, overwrite: bool = False) -> str:
    """
    Copy a file or directory tree from source to destination.
    Args:
        source: Path to the source file or directory.
        destination: Path to the destination file or directory.
        overwrite: Allow overwriting an existing destination file. Default = False.
    Returns:
        Confirmation message with source and destination paths.
    """
    src = Path(source).expanduser().resolve()
    dst = Path(destination).expanduser().resolve()

    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")

    if dst.exists() and not overwrite:
        raise FileExistsError(
            f"Destination already exists: {dst}. Set overwrite=True to replace it."
        )

    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    return f"Copied '{src}' → '{dst}'"


@mcp.tool(name="File-Move")
def move_file(source: str, destination: str, overwrite: bool = False) -> str:
    """
    Move or rename a file or directory.
    Args:
        source: Path to the source file or directory.
        destination: Path to the destination file or directory.
        overwrite: Allow overwriting an existing destination. Default = False.
    Returns:
        Confirmation message with source and destination paths.
    """
    src = Path(source).expanduser().resolve()
    dst = Path(destination).expanduser().resolve()

    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")

    if dst.exists():
        if not overwrite:
            raise FileExistsError(
                f"Destination already exists: {dst}. Set overwrite=True to replace it."
            )
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return f"Moved '{src}' → '{dst}'"


@mcp.tool(name="Dir-List")
def list_dir(
    path: str,
    show_hidden: bool = False,
    recursive: bool = False,
) -> str:
    """
    List the contents of a directory with details: type, size, permissions, and timestamps.
    Args:
        path: Absolute or relative path to the directory.
        show_hidden: Include entries whose names start with '.'. Default = False.
        recursive: Recursively list subdirectories. Default = False.
    Returns:
        A formatted multi-line string with one entry per line:
        [type] [permissions] [size_human] [modified] <relative_path>

        type        : 'DIR' for directories, 'FILE' for regular files, 'LINK' for symlinks.
        permissions : Unix-style rwx string (e.g. 'rwxr-xr-x').
        size_human  : Human-readable size (B / KB / MB / GB); directories show '—'.
        modified    : Last-modified timestamp in ISO-8601 format (YYYY-MM-DD HH:MM:SS).
    """
    base = Path(path).expanduser().resolve()
    if not base.exists():
        raise FileNotFoundError(f"Directory not found: {base}")
    if not base.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {base}")

    def _human_size(size_bytes: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size_bytes < 1024:
                return f"{size_bytes:.0f} {unit}" if unit == "B" else f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def _permissions(st: os.stat_result) -> str:
        mode = st.st_mode
        bits = [
            ("r", stat.S_IRUSR), ("w", stat.S_IWUSR), ("x", stat.S_IXUSR),
            ("r", stat.S_IRGRP), ("w", stat.S_IWGRP), ("x", stat.S_IXGRP),
            ("r", stat.S_IROTH), ("w", stat.S_IWOTH), ("x", stat.S_IXOTH),
        ]
        return "".join(c if mode & mask else "-" for c, mask in bits)

    def _entry_line(entry_path: Path) -> str:
        try:
            st = entry_path.lstat()
        except PermissionError:
            return f"{'?':4s} {'?':9s} {'?':>9s} {'?':19s} {entry_path.relative_to(base)}"

        if entry_path.is_symlink():
            kind = "LINK "
            size_str = "—"
        elif entry_path.is_dir():
            kind = "DIR  "
            size_str = "—"
        elif entry_path.is_block_device():
            kind = "DEV  "
            size_str = "—"
        elif entry_path.is_file():
            kind = "FILE "
            size_str = _human_size(st.st_size)
        else:
            kind = "OTHER"
            size_str = "—"

        perms = _permissions(st)
        modified = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        rel = entry_path.relative_to(base)
        return f"{kind}  {perms}  {size_str:>10}  {modified}  {rel}"

    lines: list[str] = [f"Directory: {base}", ""]
    header = f"{'TYPE':4}  {'PERMISSIONS':9}  {'SIZE':>10}  {'MODIFIED':19}  NAME"
    separator = "-" * len(header)
    lines += [header, separator]

    def _collect(directory: Path, depth: int = 0) -> None:
        try:
            entries = sorted(directory.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except PermissionError:
            lines.append(f"  [permission denied: {directory.relative_to(base)}]")
            return

        for entry in entries:
            if not show_hidden and entry.name.startswith("."):
                continue
            lines.append(_entry_line(entry))
            if recursive and entry.is_dir() and not entry.is_symlink():
                _collect(entry, depth + 1)

    _collect(base)
    lines.append(separator)

    # Summary counts
    all_lines = "\n".join(lines)
    files = sum(1 for l in lines if l.startswith("FILE"))
    dirs  = sum(1 for l in lines if l.startswith("DIR"))
    links = sum(1 for l in lines if l.startswith("LINK"))
    lines.append(f"  {dirs} dir(s), {files} file(s), {links} symlink(s)")

    return "\n".join(lines)