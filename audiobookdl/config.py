from dataclasses import dataclass
from typing import Optional

import tomli
import appdirs
import os


@dataclass(slots=True)
class SourceConfig:
    """Stores configuration for source"""
    username: Optional[str]
    password: Optional[str]
    library: Optional[str]


@dataclass(slots=True)
class Config:
    """audiobook-dl config"""
    sources: dict[str, SourceConfig]
    output_template: Optional[str]


def load_config() -> Config:
    """
    Load config file from disk

    :returns: Content of config file
    """
    # Load config from disk
    config_dir = appdirs.user_config_dir("audiobook-dl", "jo1gi")
    config_file = os.path.join(config_dir, "audiobook-dl.toml")
    if os.path.exists(config_file):
        with open(config_file, "rb") as f:
            config_dict = tomli.load(f)
    else:
        config_dict = {}
    # Add sources
    sources: dict[str, SourceConfig] = {}
    if "sources" in config_dict:
        for source_name, values in config_dict["sources"].items():
            sources[source_name] = SourceConfig (
                username = values.get("username"),
                password = values.get("password"),
                library = values.get("library")
            )
    # Create config object
    return Config(
        sources = sources,
        output_template = config_dict.get("output_template")
    )
