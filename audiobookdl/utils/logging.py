import rich

global_loglevel = 1
LOGLEVELS = ["debug", "info", "warning", "error"]
LOG_MSGS = [
        "[yellow bold]DEBUG[/yellow bold] {msg}",
        "{msg}",
        "[orange bold]WARNING[/orange bold] {msg}",
        "[red bold]ERROR[/red bold] {msg}",
        ]

def set_loglevel(loglevel):
    global global_loglevel
    new = get_loglevel(loglevel)
    if not loglevel == None:
        global_loglevel = new

def get_loglevel(loglevel):
    """Converts `loglevel` to a number value"""
    if loglevel in LOGLEVELS:
        return LOGLEVELS.index(loglevel)
    else:
        log(f"Unknown loglevel: {loglevel}", "warning")

def log(msg, level="info"):
    """Displays the msg if the level is high enough"""
    level_num = get_loglevel(level)
    if global_loglevel <= level_num:
        rich.print(LOG_MSGS[level_num].format(msg=msg))

def error(msg):
    """Show error message"""
    log(msg, "error")
