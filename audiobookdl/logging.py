from rich.console import Console
from rich.progress import Progress, ProgressColumn
import importlib.resources
from typing import Union

debug_mode = False
quiet_mode = False
ffmpeg_output = False
console = Console(stderr=True)

def debug(msg: str):
    """Print debug msg"""
    if debug_mode:
        log(f"[yellow bold]DEBUG[/] {msg}")


def log(msg: str):
    """Display msg in log"""
    if not quiet_mode:
        console.print(msg)


def read_asset_file(path: str) -> str:
    return importlib.resources.files("audiobookdl") \
        .joinpath(path) \
        .read_text(encoding="utf8")


def error(msg: str):
    console.print(msg)


def print_error_file(name: str, **kwargs):
    """Print predefined error message"""
    msg = read_asset_file(f"assets/errors/{name}.txt").format(**kwargs)
    msg = msg.strip()
    error(msg)


def print_asset_file(path: str):
    """Read asset file and print it"""
    console.print(read_asset_file(path))


def simple_help():
    """Print basic help information"""
    print_asset_file("assets/simple_help.txt")

def progress(progress_format: list[Union[str, ProgressColumn]]) -> Progress:
    return Progress(*progress_format, console=console)
