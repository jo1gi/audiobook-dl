from rich.console import Console

debug_mode = False
quiet_mode = False
console = Console(stderr=True)

def debug(msg: str):
    """Print debug msg"""
    if debug_mode:
        log(f"[yellow bold]DEBUG[/] {msg}")

def log(msg: str):
    """Display msg in log"""
    if not quiet_mode:
        console.print(msg)
