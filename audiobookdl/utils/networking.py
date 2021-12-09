import json
import requests
import os
import rich


def post(self, url, **kwargs):
    resp = self._session.post(url, **kwargs)
    return resp.content


def get(self, url, **kwargs):
    resp = self._session.get(url, **kwargs)
    if resp.status_code == 200:
        return resp.content
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


def get_stream_files(self, url, **kwargs):
    """Creates a list of files from a HLS playlist"""
    resp = self._session.get(url, **kwargs)
    if not (resp.status_code == 200 or resp.status_code == 304):
        return []
    content = resp.content.decode("utf-8")
    parent = os.path.dirname(url)
    def create_file_description(n, f):
        return {
            "url": f"{parent}/{f}",
            "ext": os.path.splitext(f)[1][1:],
            "part": n,
        }
    files = []
    for n,f in enumerate(filter(lambda x: len(x)>0 and not x[0] == "#", content.split("\n"))):
        files.append(create_file_description(n,f))
    return files
