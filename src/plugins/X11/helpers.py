import subprocess
import tempfile
import os
from PIL import Image
from typing import Union
from typing import Any, Dict, List, Optional
from Xlib import Xatom, error


def get_window_list_by_property(display, root, atom_name: str) -> List[int]:
    try:
        atom = display.intern_atom(atom_name)
        prop = root.get_full_property(atom, Xatom.WINDOW)
        if prop and prop.value:
            return [int(x) for x in prop.value]
    except error.XError:
        pass
    except Exception:
        pass
    return []


def screenshot_window_by_id(window_id: Union[str, int]) -> (Image.Image, str):
    """
    Take a screenshot of an X11 window by its window ID and return as PIL Image.

    Args:
        window_id: Window ID as hex string (e.g., "0x300004a") or integer

    Returns:
        PIL.Image: Screenshot of the specified window
        str: Window metadata(position and size)

    Raises:
        ValueError: If window_id is invalid or window not found
        RuntimeError: If screenshot capture fails
        FileNotFoundError: If required tools are not installed
    """

    # Convert window_id to proper format for xwininfo/import
    if isinstance(window_id, int):
        window_id = hex(window_id)
    elif isinstance(window_id, str):
        if not window_id.startswith('0x'):
            # Assume it's a decimal number
            try:
                window_id = hex(int(window_id))
            except ValueError:
                raise ValueError(f"Invalid window ID format: {window_id}")

    # Verify the window exists
    try:
        result = subprocess.run(
            ['xwininfo', '-id', window_id, '-size', '-stats'],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.split("\n")
        info = "\n".join(lines[1:3] + lines[24:30])

    except subprocess.CalledProcessError as e:
        raise ValueError(f"Window with ID {window_id} not found or invalid") from e
    except FileNotFoundError:
        raise FileNotFoundError("xwininfo not found. Please install x11-utils package.")

    # Create temporary file for screenshot
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Take screenshot using import command (part of ImageMagick)
        subprocess.run(
            ['import', '-window', window_id, temp_path],
            check=True,
            capture_output=True
        )

        # Load and return PIL Image
        image = Image.open(temp_path)
        # Load the image data into memory so we can delete the temp file
        image.load()

        return image, info

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to capture screenshot: {e}") from e
    except FileNotFoundError:
        raise FileNotFoundError("import command not found. Please install imagemagick package.")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def screenshot_window_by_id_xwd(window_id: Union[str, int]) -> Image.Image:
    """
    Alternative implementation using xwd instead of ImageMagick's import.
    This might work better in some environments.

    Args:
        window_id: Window ID as hex string (e.g., "0x300004a") or integer

    Returns:
        PIL.Image: Screenshot of the specified window
    """

    # Convert window_id to proper format
    if isinstance(window_id, int):
        window_id = hex(window_id)
    elif isinstance(window_id, str):
        if not window_id.startswith('0x'):
            try:
                window_id = hex(int(window_id))
            except ValueError:
                raise ValueError(f"Invalid window ID format: {window_id}")

    # Create temporary file for screenshot
    with tempfile.NamedTemporaryFile(suffix='.xwd', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Take screenshot using xwd
        subprocess.run(
            ['xwd', '-id', window_id, '-out', temp_path],
            check=True,
            capture_output=True
        )

        # Convert xwd to PNG using ImageMagick
        png_path = temp_path + '.png'
        subprocess.run(
            ['convert', temp_path, png_path],
            check=True,
            capture_output=True
        )

        # Load and return PIL Image
        image = Image.open(png_path)
        image.load()

        return image

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to capture screenshot: {e}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError("Required tools not found. Install x11-apps and imagemagick packages.") from e
    finally:
        # Clean up temporary files
        for path in [temp_path, temp_path + '.png']:
            if os.path.exists(path):
                os.unlink(path)
