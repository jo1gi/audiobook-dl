import sys
import dataclasses

# Make dataclasses use slots, if python version is equal to or above 3.10
py310 = sys.version_info >= (3, 10)
dataclass_options = {"slots": True} if py310 else {}
dataclass = dataclasses.dataclass(**dataclass_options)
