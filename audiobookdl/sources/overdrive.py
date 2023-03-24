from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover
from audiobookdl.exceptions import DataNotPresent, UserNotAuthorized

import re
import json
from urllib3.util import parse_url


class OverdriveSource(Source):
    match = [
        r"https://.+\.listen\.overdrive\.com"
    ]

    names = [ "Overdrive", "Libby" ]

    def prepare(self):
        # Parse url
        parsed_url = parse_url(self.url)
        hostname = parsed_url.hostname
        self.prefix = f"https://{hostname}"
        # Extract json from javascript
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


    def get_metadata(self) -> AudiobookMetadata:
        title = self.meta["title"]["main"]
        metadata = AudiobookMetadata(title)
        for creator in self.meta["creator"]:
            if creator["role"] == "author":
                metadata.add_author(creator["name"])
            if creator["role"] == "narrator":
                metadata.add_narrator(creator["name"])
        return metadata

    def get_cover(self) -> Cover:
        cover_url = self.prefix + self.meta['-odread-furbish-uri']
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")

    def _get_previous_length(self, index) -> int:
        """Returns the ending point of the previous part"""
        if index == 0:
            return 0
        return self._get_previous_length(index-1) + \
            self.meta["spine"][index-1]["audio-duration"]

    def get_chapters(self) -> list[Chapter]:
        chapters = []
        for chapter in self.meta["nav"]["toc"]:
            timepoint = 0.
            if '#' in chapter["path"]:
                timepoint = float(chapter["path"].split("#")[1])
            part_result = re.search(r"(?<=(Part))\d+", chapter["path"])
            if part_result is None:
                continue
            part = int(part_result.group(0))-1
            start = int((self._get_previous_length(part)+timepoint)*1000)
            chapters.append(Chapter(start, chapter["title"]))
        return chapters

    def get_files(self) -> list[AudiobookFile]:
        files = []
        for num, part in enumerate(self.meta["spine"]):
            files.append(AudiobookFile(
                url = f"{self.prefix}/{part['path']}",
                title = self.toc[num],
                ext = "mp3"
            ))
        return files
