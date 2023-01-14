from .source import Source
from audiobookdl import  AudiobookFile, logging
from audiobookdl.exceptions import UserNotAuthorized, RequestError

from typing import Dict, Optional, List
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

    def get_files(self) -> List[AudiobookFile]:
        if not self.book_id:
            return []
        return self.get_stream_files(
            f"https://audio.api.streaming.pubhub.dk/v1/stream/hls/{self.book_id}/playlist.m3u8"
        )

    def before(self):
        ajax: Optional[Dict] = self.get_json(f"{self.url}/listen/ajax")
        if not ajax:
            raise RequestError
        logging.debug(f"{ajax=}")
        if ajax[1]["title"] != "Lyt":
            raise UserNotAuthorized
        id_match = re.search(r"(?<=(o=))[0-9a-f\-]+", ajax[1]["data"])
        if id_match and id_match.group():
            self.book_id = id_match.group()
            logging.debug(f"{self.book_id=}")
        else:
            logging.debug("Could not find book id")
            raise UserNotAuthorized
        self.meta: Optional[Dict] = self.get_json(f"https://audio.api.streaming.pubhub.dk/v1/orders/{self.book_id}")
        logging.debug(f"{self.meta=}")
