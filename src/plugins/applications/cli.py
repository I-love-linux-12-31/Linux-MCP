import asyncio
import os
import shlex
import signal
import time
from typing import Optional

from src.modules.init_system import get_mcp

mcp = get_mcp()


DEFAULT_TIMEOUT = 30  # seconds
MAX_TIMEOUT = 600     # hard cap (10 minutes)
MAX_OUTPUT_BYTES = 1_000_000  # 1 MB per stream


def _truncate(text: str, limit: int = MAX_OUTPUT_BYTES) -> tuple[str, bool]:
    """Truncate text to *limit* bytes; return (text, was_truncated)."""
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text, False
    return encoded[:limit].decode("utf-8", errors="replace"), True


async def _run(
    command: str,
    *,
    timeout: float,
    cwd: Optional[str],
    env: Optional[dict[str, str]],
    shell: bool,
    stdin_data: Optional[str],
) -> dict:
    """
    Core async runner. Returns a structured result dict.
    """
    merged_env = {**os.environ, **(env or {})}

    start = time.monotonic()
    proc = None
    timed_out = False

    try:
        if shell:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if stdin_data else asyncio.subprocess.DEVNULL,
                cwd=cwd,
                env=merged_env,
                preexec_fn=os.setsid,  # own process group for clean kill
            )
        else:
            args = shlex.split(command)
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if stdin_data else asyncio.subprocess.DEVNULL,
                cwd=cwd,
                env=merged_env,
                preexec_fn=os.setsid,
            )

        stdin_bytes = stdin_data.encode() if stdin_data else None

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            timed_out = True
            # Kill the entire process group
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout_bytes, stderr_bytes = await proc.communicate()

    except FileNotFoundError as exc:
        elapsed = time.monotonic() - start
        return {
            "success": False,
            "exit_code": 127,
            "stdout": "",
            "stderr": f"Command not found: {exc}",
            "timed_out": False,
            "elapsed_seconds": round(elapsed, 3),
            "pid": None,
            "command": command,
            "error": str(exc),
        }
    except PermissionError as exc:
        elapsed = time.monotonic() - start
        return {
            "success": False,
            "exit_code": 126,
            "stdout": "",
            "stderr": f"Permission denied: {exc}",
            "timed_out": False,
            "elapsed_seconds": round(elapsed, 3),
            "pid": None,
            "command": command,
            "error": str(exc),
        }

    elapsed = time.monotonic() - start
    stdout_str = stdout_bytes.decode("utf-8", errors="replace")
    stderr_str = stderr_bytes.decode("utf-8", errors="replace")

    stdout_str, stdout_truncated = _truncate(stdout_str)
    stderr_str, stderr_truncated = _truncate(stderr_str)

    exit_code = proc.returncode if not timed_out else -1

    result = {
        "success": exit_code == 0,
        "exit_code": exit_code,
        "stdout": stdout_str,
        "stderr": stderr_str,
        "timed_out": timed_out,
        "elapsed_seconds": round(elapsed, 3),
        "pid": proc.pid,
        "command": command,
    }
    if stdout_truncated:
        result["stdout_truncated"] = True
    if stderr_truncated:
        result["stderr_truncated"] = True
    return result


@mcp.tool()
async def list_processes(
    filter_name: Optional[str] = None,
    top_n: int = 20,
) -> dict:
    """
    List running processes on the system.

    Args:
        filter_name: Optional substring to filter process names (case-insensitive).
        top_n: Maximum number of processes to return (default 20, max 200).

    Returns:
        {"processes": [ {"pid", "user", "cpu", "mem", "command"}, ... ]}
    Keywords: programs, processes, task_manager, process, task, top, application, applications, Linux-MCP
    """
    top_n = min(max(1, top_n), 200)
    ps_cmd = "ps aux --no-headers"
    result = await _run(ps_cmd, timeout=10, cwd=None, env=None, shell=True, stdin_data=None)
    if not result["success"]:
        return {"error": result["stderr"], "processes": []}

    processes = []
    for line in result["stdout"].splitlines():
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        user, pid, cpu, mem, *_, command = parts[0], parts[1], parts[2], parts[3], parts[10]
        if filter_name and filter_name.lower() not in command.lower():
            continue
        processes.append({"pid": pid, "user": user, "cpu": cpu, "mem": mem, "command": command})
        if len(processes) >= top_n:
            break

    return {"processes": processes, "count": len(processes)}


@mcp.tool()
async def run_command(
    command: str,
    timeout: float = DEFAULT_TIMEOUT,
    working_directory: Optional[str] = None,
    environment: Optional[dict[str, str]] = None,
    stdin: Optional[str] = None,
    use_shell: bool = True,
) -> dict:
    """
    Run a shell command and return structured output. This tool is NOT designed to run long-term applications.

    Args:
        command: The shell command to execute (e.g. "ls -la /tmp").
        timeout: Maximum seconds to wait before killing the process (default 30, max 600).
        working_directory: Directory to run the command in. Defaults to current directory.
        environment: Extra environment variables to inject (merged with current env).
        stdin: Optional text to pipe into the command's standard input.
        use_shell: If True (default) run via /bin/sh so pipes, redirects, globs work.
                   Set False to exec the binary directly (safer, but no shell features).

    Returns:
        {
            "success": bool,
            "exit_code": int,
            "stdout": str,
            "stderr": str,
            "timed_out": bool,
            "elapsed_seconds": float,
            "pid": int | None,
            "command": str
        }
    Keywords: programs, processes, application, applications, script, shell, bash, command, execute, call, start, Linux-MCP
    """

    timeout = min(max(0.1, timeout), MAX_TIMEOUT)

    if working_directory and not os.path.isdir(working_directory):
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Working directory does not exist: {working_directory}",
            "timed_out": False,
            "elapsed_seconds": 0.0,
            "pid": None,
            "command": command,
            "error": "invalid_cwd",
        }

    return await _run(
        command,
        timeout=timeout,
        cwd=working_directory,
        env=environment,
        shell=use_shell,
        stdin_data=stdin,
    )