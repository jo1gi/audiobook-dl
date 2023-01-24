from .source import Source
from audiobookdl import AudiobookFile
from audiobookdl.exceptions import DataNotPresent, UserNotAuthorized

import re
import json
from typing import List


class OverdriveSource(Source):
    match = [
        r"https://.+\.listen\.overdrive\.com"
    ]

    names = [ "Overdrive" ]

    def before(self):
        prefix_re = re.search(self.match[0], self.url)
        if prefix_re and prefix_re.group(0):
            self.prefix = prefix_re.group(0)
        else:
            raise DataNotPresent
        raw = self.find_in_page(self.url, 'window.bData = {.+;')
        if raw is None:
            raise UserNotAuthorized
        raw_trimmed = raw[15:-1]
        self.meta = json.loads(raw_trimmed)
        # Table of contents
        self.toc = []
        for part in self.meta["nav"]["toc"]:
            if "contents" in part:
                self.toc = []
                for _ in range(len(self.meta["spine"])):
                    self.toc.append(self.meta["nav"]["toc"][0]["title"])
                break
            else:
                self.toc.append(part["title"])

    def get_title(self) -> str:
        return self.meta["title"]["main"]

    def get_metadata(self):
        authors = []
        narrators = []
        for creator in self.meta["creator"]:
            if creator["role"] == "author":
                authors.append(creator["name"])
            if creator["role"] == "narrator":
                narrators.append(creator["name"])
        return {
            'author': authors,
            'narrator': narrators
        }

    def get_cover(self) -> bytes:
        cover_url = self.prefix + self.meta['-odread-furbish-uri']
        return self.get(cover_url)

    def _get_previous_length(self, index) -> int:
        """Returns the ending point of the previous part"""
        if index == 0:
            return 0
        return self._get_previous_length(index-1) + \
            self.meta["spine"][index-1]["audio-duration"]

    def get_chapters(self):
        chapters = []
        for chapter in self.meta["nav"]["toc"]:
            timepoint = 0
            if '#' in chapter["path"]:
                timepoint = float(chapter["path"].split("#")[1])
            part = int(re.search(
                r"(?<=(Part))\d+", chapter["path"]).group(0))-1
            start = (self._get_previous_length(part)+timepoint)*1000
            chapters.append((start, chapter["title"]))
        return chapters

    def get_files(self) -> List[AudiobookFile]:
        files = []
        for num, part in enumerate(self.meta["spine"]):
            files.append(AudiobookFile(
                url = f"{self.prefix}/{part['path']}",
                title = self.toc[num],
                ext = "mp3"
            ))
        return files
