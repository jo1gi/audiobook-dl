import json
import os
import m3u8
from . import logging

def post(self, url, **kwargs):
    resp = self._session.post(url, **kwargs)
    return resp.content


def get(self, url, **kwargs):
    resp = self._session.get(url, **kwargs)
    if resp.status_code == 200:
        return resp.content
    logging.debug(f"Failed to download data from: {url}\nResponse:\n{resp.content}")
    return None


def post_json(self, url, **kwargs):
    """Downloads data with the given url and converts it to json"""
    resp = self.post(url, **kwargs)
    if resp is None:
        return None
    return json.loads(resp.decode('utf8'))


def get_json(self, url, **kwargs):
    """Downloads data with the given url and converts it to json"""
    resp = self.get(url, **kwargs)
    if resp is None:
        return None
    return json.loads(resp.decode('utf8'))

def get_stream_files(self, url, headers={}, **kwargs):
    """Creates a list of audio files from an m3u8 file"""
    playlist = m3u8.load(url, headers=headers)
    files = []
    for n, seg in enumerate(playlist.segments):
        current = {
            "url": seg.absolute_uri,
            "part": n,
            "ext": os.path.splitext(seg.absolute_uri)[1][1:],
            "headers": headers,
        }
        if seg.key:
            current["encryption_key"] = self._get_page(seg.key.absolute_uri, headers=headers)
            current["iv"] = int(seg.key.iv, 0).to_bytes(16, byteorder='big')
        files.append(current)
    return files
