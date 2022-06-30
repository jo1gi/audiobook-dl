from ..utils.source import Source
from ..utils.exceptions import UserNotAuthenticated, RequestError
from ..utils.logging import debug

from typing import Dict, Optional
import re

class EreolenSource(Source):
    match = [
        r"https?://ereolen.dk/ting/object/.+"
    ]
    require_cookies = True

    def get_title(self):
        if not self.meta:
            return None
        return self.meta["title"]

    def get_metadata(self):
        if not self.meta:
            return {}
        metadata = {
            "author": self.meta["artist"]
        }
        return metadata

    def get_cover(self):
        if not self.meta:
            return None
        return self.get(self.meta["cover"])

    def get_files(self):
        if not self.book_id:
            return None
        return self.get_stream_files(
            f"https://audio.api.streaming.pubhub.dk/v1/stream/hls/{self.book_id}/playlist.m3u8"
        )

    def before(self):
        ajax: Optional[Dict] = self.get_json(f"{self.url}/listen/ajax")
        if not ajax:
            raise RequestError
        debug(f"{ajax=}")
        if ajax[1]["title"] != "Lyt":
            raise UserNotAuthenticated
        id_match = re.search(r"(?<=(o=))[0-9a-f\-]+", ajax[1]["data"])
        if id_match and id_match.group():
            self.book_id = id_match.group()
            debug(f"{self.book_id=}")
        else:
            debug("Could not find book id")
            raise UserNotAuthenticated
        self.meta: Optional[Dict] = self.get_json(f"https://audio.api.streaming.pubhub.dk/v1/orders/{self.book_id}")
        debug(f"{self.meta=}")
