from audiobookdl.exceptions import ConfigNotFound
from attrs import define, Factory

from typing import Dict, Optional

import tomli
import platformdirs
import os


@define
class SourceConfig:
    """Stores configuration for source"""
    username: Optional[str]
    password: Optional[str]
    library: Optional[str]
    cookie_file: Optional[str]


@define
class Config:
    """audiobook-dl config"""
    sources: Dict[str, SourceConfig]
    output_template: Optional[str]
    database_directory: Optional[str]
    skip_downloaded: Optional[bool]
    combine: Optional[bool]
    remove_chars: Optional[str]
    no_chapters: Optional[bool]
    output_format: Optional[str]
    write_json_metadata: Optional[bool]
    mp4_audio_encoder: Optional[str]


def load_config(overwrite: Optional[str]) -> Config:
    """
    Load config file from disk

    :param overwrite: Optional alternative location of config file
    :returns: Content of config file
    :raises: ConfigNotFound if location does not exists
    """
    config_location = get_config_location(overwrite)
    config_dict = read_config(config_location)
    return structure_config(config_location, config_dict)


def config_dir() -> str:
    """
    Get path of configuration directory

    :returns: Path of configuration directory
    """
    return platformdirs.user_config_dir("audiobook-dl", "jo1gi")


def get_config_location(overwrite: Optional[str]) -> str:
    """
    Get path of configuration file

    :param overwrite: Overwrite of default configuration file location
    :returns: Path of configuration file
    """
    if overwrite:
        if not os.path.exists(overwrite):
            raise ConfigNotFound
        return overwrite
    return os.path.join(config_dir(), "audiobook-dl.toml")


def read_config(config_file: str) -> dict:
    """
    Read config from disk as dictionary

    :param location: Location of configuration file
    :returns: Content of config file as dictionary
    :raises: ConfigNotFound if location does not exists
    """
    if os.path.exists(config_file):
        with open(config_file, "rb") as f:
            config_dict = tomli.load(f)
    else:
        config_dict = {}
    return config_dict


def structure_config(config_location: str, config_dict: dict) -> Config:
    """
    Structure configuration file content as `Config`

    :param config_dict: Configuration file as a dictionary
    :returns: Configuration file `Config`
    """
    # Add sources
    sources: Dict[str, SourceConfig] = {}
    if "sources" in config_dict:
        for source_name, values in config_dict["sources"].items():
            cookie_file = values.get("cookie_file")
            if cookie_file:
                cookie_file = os.path.relpath(values.get("cookie_file"), start=config_location)
            sources[source_name] = SourceConfig(
                username = values.get("username"),
                password = values.get("password"),
                library = values.get("library"),
                cookie_file = cookie_file
            )
    # Create config object
    return Config(
        sources = sources,
        output_template = config_dict.get("output_template"),
        database_directory = config_dict.get("database_directory"),
        skip_downloaded = config_dict.get("skip_downloaded"),
        combine = config_dict.get("combine"),
        remove_chars = config_dict.get("remove_chars"),
        no_chapters = config_dict.get("no_chapters"),
        output_format = config_dict.get("output_format"),
        write_json_metadata = config_dict.get("write_json_metadata"),
        mp4_audio_encoder = config_dict.get("mp4_audio_encoder"),
    )
