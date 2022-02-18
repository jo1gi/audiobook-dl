import rich

debug_mode = False
quiet_mode = False

def debug(msg: str):
    """Print debug msg"""
    if debug_mode:
        log(f"[yellow bold]DEBUG[/] {msg}")

def log(msg: str):
    """Display msg in log"""
    if not quiet_mode:
        rich.print(msg)
