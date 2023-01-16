import functools
from typing import List

@functools.cache
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

def nearest_string(s: str, l: List[str]) -> str:
    return sorted(l, key = lambda x: levenstein_distance(s, x))[0]
