from .source import Source
from audiobookdl import AudiobookFile, logging
from audiobookdl.exceptions import NoSourceFound, UserNotAuthorized

import re
from typing import List

class ChapterSource(Source):
    _authentication_methods = [
        "login"
    ]

    names = [ "chapter.dk" ]

    match = [
        r"https://chapter.dk/bog/\d+"
    ]

    def _login(self, username, password):
        auth_resp = self.post_json(
            "https://api.prod.chapter.beat.no/v2/oauth2/token",
            data = {
                "username": username,
                "password": password,
                "grant_type": "password",
                "client_secret": "b1e795a047c00a0170b2d41cdc1a04237c0b499f",
                "client_id": "e8041ed18678d963428eda7645b5367d"
            }
        )
        if not "access_token" in auth_resp:
            raise UserNotAuthorized
        access_token: str = auth_resp["access_token"]
        self.headers = { "Authorization": f"Bearer {access_token}" }

    def get_title(self) -> str:
        return self.meta["title"]

    def get_metadata(self):
        authors = [i["name"] for i in self.meta["actors"] if i["role"] == "author"]
        narrators = [i["name"] for i in self.meta["actors"] if i["role"] == "narrator"]
        return {
            "authors": authors,
            "narrators": narrators
        }

    def get_files(self) -> List[AudiobookFile]:
        files = []
        for track in self.meta["tracks"]:
            url_resp = self.get_json(
                f"https://api.prod.chapter.beat.no/v2/streams/offline/{track['id']}",
                headers=self.headers
            )
            files.append(AudiobookFile(
                url = url_resp["stream"]["url"],
                title = track["title"],
                ext = "m4v"
            ))
        return files

    def get_cover(self) -> bytes:
        return self.get(self.meta["cover"]["w800"])

    def before(self):
        id_match = re.search(r"bog/(\d+)", self.url)
        if id_match and id_match.group(1):
            iden = id_match.group(1)
            logging.debug(f"{iden=}")
        else:
            raise NoSourceFound
        self.meta = self.get_json(
            f"https://api.prod.chapter.beat.no/v2/releases/{iden}",
            headers={**self.headers, "X-Release-Cover-Sizes": "w800"}
        )["release"]
