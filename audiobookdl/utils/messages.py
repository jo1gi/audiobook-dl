from rich.console import Console
from rich import print
import pkg_resources

def read_asset_file(path) -> str:
    return pkg_resources.resource_string("audiobookdl", path).decode("utf8")

def print_asset_file(path):
    print(read_asset_file(path))

def print_error(name, **kwargs):
    console = Console(stderr=True)
    msg = read_asset_file(f"assets/errors/{name}.txt").format(**kwargs)
    console.print(msg)

def simple_help():
    print_asset_file("assets/simple_help.txt")
