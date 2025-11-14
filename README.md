# Linux-MCP
MCP server to provide lots of tools for LLM and Linux integration. 
> [!CAUTION]
> This MCP server provide to LLM tools, that can damage your data or device. **You run this software on your risk!**

## Functionality
> [!WARNING]
> Wayland is not fully supported! Use X11.
### Applications
+ [X] Interact wih GUI applications
+ [ ] Interact with cli applications
+ [X] Get application info (GUI)
### UI Automatization
+ [X] Cursor manipulation
+ [X] Keyboard manipulation
+ [X] Windows manipulation
+ [X] Clipboard interaction
### Filesystem
+ [ ] Read file
+ [ ] Write file
+ [ ] Update file
+ [ ] Copy/paste tool
+ [ ] Move files tool
+ [X] call to open file/folder

```mermaid
flowchart LR
    mcp(Linux MCP)
    g_fs([Files system tools])
    g_de([Window and screen capture, \nDE/X11 manipulation tools])
    g_clipboard([Clipboard interaction tools])
    g_cursor([Cursor manipulation tools])
    g_keyboard([Keyboard input emulation tools])
    g_applications([Applications manipulation tools])
    g_misc([Other tools])
    
    mcp --- g_misc 
    mcp --- g_fs
    mcp --- g_de
    mcp --- g_clipboard
    mcp --- g_keyboard
    mcp --- g_cursor
    mcp --- g_applications
        
    subgraph clipboard tools
        g_clipboard_get_text([Clipboard-Get-Text]) --> g_clipboard
        g_clipboard_set_text([Clipboard-Set-Text]) --> g_clipboard
        g_clipboard_get_image([Clipboard-Get-Image]) --> g_clipboard
        g_clipboard_get_image([Clipboard-Copy-Image]) --> g_clipboard
        
        g_clipboard_paste-ctrlv([Clipboard-Paste-CtrlV]) --> g_clipboard
        g_clipboard_paste-ctrlshiftv([Clipboard-Paste-CtrlShiftV]) --> g_clipboard
    end
    
    subgraph cursor tools
        g_cursor_move([Cursor-Move]) --> g_cursor
        g_cursor_click([Cursor-Click]) --> g_cursor
        g_cursor_drag_and_drop([Cursor-Drag-And-Drop]) --> g_cursor
        g_cursor_get_position([Cursor-Get-Position]) --> g_cursor
    end
    
    subgraph keyboard tools
        g_keyboard_single_key_press([Keyboard-Single-Key-Press]) --> g_keyboard
        g_keyboard_hotkey_press([Keyboard-Hotkey-Press]) --> g_keyboard
        g_keyboard_type_line_of_text([Keyboard-Type-Line-Of-Text]) --> g_keyboard
        g_keyboard_type_text([Keyboard-Type-Text]) --> g_keyboard
    end
    
    subgraph misc 
        wait([Wait]) --> g_misc
        call_to_open_uri([Call-To-Open-URI]) --> g_misc
    end
    
    subgraph DE and graphics server API tools 
        g_de_desktop_state_common([Desktop-State-Common]) --> g_de
        g_de_window_get_image([Window-Get-Image]) --> g_de
        g_de_desktop_get_image([Desktop-Get-Image]) --> g_de
        g_de_desktop_get_image_compressed([Desktop-Get-Image-Compressed]) --> g_de
        g_de_desktop_get_image --> g_de_desktop_get_image_compressed
        
        subgraph window interaction
            g_de_window_move([Window-Move]) --> g_de
            g_de_window_resize([Window-Resize]) --> g_de
            g_de_window_focus([Window-Focus]) --> g_de
            g_de_window_close([Window-Close]) --> g_de
            g_de_window_toggle_fullscreen([Window-Toggle-Fullscreen]) --> g_de    
        end
        
    end
    
    subgraph applications manipulation tools 
        g_applications_get_list([Applications-Get-List]) --> g_applications
        g_applications_get_info([Applications-Get-Info]) --> g_applications
        g_applications_start([Applications-Start]) --> g_applications
    end
    
    %%classDef animate stroke-dasharray: 9, 5 ,stroke-dashoffset: 900,animation: dash 25s linear infinite;
    %% class line1 animate
```

## Install
### Ubuntu
> [!WARNING]
> For ubuntu, you need to install [uv](https://github.com/astral-sh/uv) manually!  
```bash
sudo apt update 
sudo apt install python3-full gnome-screenshot imagemagick
# Place application to installation directory
cd /path/to/application/dir
./install.sh # to add Linux-MCP to client applications like Claude-desktop, vscode and other
```

### Fedora
```bash
sudo dnf install python3 uv gnome-screenshot ImageMagick
# Place application to installation directory
cd /path/to/application/dir
./install.sh # to add Linux-MCP to client applications like Claude-desktop, VScode and others
```

### Author: Yaroslav Kuznetsov