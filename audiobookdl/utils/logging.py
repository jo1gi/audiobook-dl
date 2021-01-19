import rich
from rich.console import Console

_console = Console()
_status = _console.status("asd")

def error(msg):
    rich.print(f"[[red]ERROR[/red]] {msg}")

def info(msg):
    _console.print(f"{msg}")

def status(msg):
    pass
