from audiobookdl import AudiobookFile, exceptions, logging
from audiobookdl.utils.audiobook import AESEncryption

from typing import Dict, List
import json
import os
import m3u8
import requests


def post(self, url: str, **kwargs) -> bytes:
    """Make post request with `Source` session"""
    resp = self._session.post(url, **kwargs)
    if resp.status_code == 200:
        return resp.content
    logging.debug(f"Failed to download data from: {url}\nResponse:\n{resp.content}")
    raise exceptions.RequestError


def get(self, url: str, force_cookies: bool = False, **kwargs) -> bytes:
    """Make get request with `Source` session"""
    if force_cookies:
        resp = self._session.get(
            url,
            cookies=_get_all_cookies(self._session),
            **kwargs
        )
    else:
        resp = self._session.get(url, **kwargs)
    if resp.status_code == 200:
        return resp.content
    logging.debug(f"Failed to download data from: {url}\nResponse:\n{resp.content}")
    raise exceptions.RequestError


def post_json(self, url: str, **kwargs) -> dict:
    """Downloads data with the given url and converts it to json"""
    resp = self.post(url, **kwargs)
    return json.loads(resp.decode('utf8'))


def get_json(self, url: str, **kwargs) -> dict:
    """Downloads data with the given url and converts it to json"""
    resp = self.get(url, **kwargs)
    return json.loads(resp.decode('utf8'))


def get_stream_files(self, url: str, headers={}) -> List[AudiobookFile]:
    """Creates a list of audio files from an m3u8 file"""
    playlist = m3u8.load(url, headers=headers)
    files = []
    for _, seg in enumerate(playlist.segments):
        current = AudiobookFile(
            url = seg.absolute_uri,
            ext = os.path.splitext(seg.absolute_uri)[1][1:].split("?")[0],
            headers = headers
        )
        if not seg.key.method == "NONE":
            current.encryption_method = AESEncryption(
                key = self._get_page(seg.key.absolute_uri, headers=headers),
                iv = int(seg.key.iv, 0).to_bytes(16, byteorder='big')
            )
        files.append(current)
    return files


def _get_all_cookies(session: requests.Session) -> Dict[str, str]:
    """
    Retrieves all cookies from session

    :returns: Dictionary of cookies
    """
    cookies = {}
    for cookie in session.cookies:
        cookies[cookie.name] = str(cookie.value)
    return cookies
