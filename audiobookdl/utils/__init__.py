import importlib.resources

def levenstein_distance(a: str, b: str) -> int:
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)
    if a[0] == b[0]:
        return levenstein_distance(a[1:], b[1:])
    return 1 + min(
        levenstein_distance(a, b[1:]), # Character is inserted
        levenstein_distance(a[1:], b), # Character is deleted
        levenstein_distance(a[1:], b[1:]) # Character is replaced
    )

def nearest_string(s: str, l: list[str]) -> str:
    return sorted(l, key = lambda x: levenstein_distance(s, x))[0]


def read_asset_file(path: str) -> str:
    return importlib.resources.files("audiobookdl") \
        .joinpath(path) \
        .read_text(encoding="utf8")
