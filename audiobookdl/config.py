from audiobookdl.exceptions import ConfigNotFound
from attrs import define, Factory

from typing import Dict, Optional

import tomli
import appdirs
import os


@define
class SourceConfig:
    """Stores configuration for source"""
    username: Optional[str]
    password: Optional[str]
    library: Optional[str]


@define
class Config:
    """audiobook-dl config"""
    sources: Dict[str, SourceConfig]
    output_template: Optional[str]


def read_config(location: Optional[str]) -> dict:
    """
    Read config from disk as dictionary

    :param location: Optional alternative location of config file
    :returns: Content of config file as dictionary
    :raises: ConfigNotFound if location does not exists
    """
    if location:
        if not os.path.exists(location):
            raise ConfigNotFound
        config_file = location
    else:
        config_dir = appdirs.user_config_dir("audiobook-dl", "jo1gi")
        config_file = os.path.join(config_dir, "audiobook-dl.toml")
    if os.path.exists(config_file):
        with open(config_file, "rb") as f:
            config_dict = tomli.load(f)
    else:
        config_dict = {}
    return config_dict



def load_config(location: Optional[str]) -> Config:
    """
    Load config file from disk

    :param location: Optional alternative location of config file
    :returns: Content of config file
    :raises: ConfigNotFound if location does not exists
    """
    config_dict = read_config(location)
    # Add sources
    sources: Dict[str, SourceConfig] = {}
    if "sources" in config_dict:
        for source_name, values in config_dict["sources"].items():
            sources[source_name] = SourceConfig(
                username = values.get("username"),
                password = values.get("password"),
                library = values.get("library")
            )
    # Create config object
    return Config(
        sources = sources,
        output_template = config_dict.get("output_template")
    )
