from .source import Source
from audiobookdl import AudiobookFile, Chapter, logging, AudiobookMetadata, Cover
from audiobookdl.exceptions import UserNotAuthorized, RequestError, DataNotPresent
from typing import Optional

import io
from PIL import Image

class ScribdSource(Source):
    match = [
        r"https?://(www.)?scribd.com/listen/\d+",
        r"https?://(www.)?scribd.com/audiobook/\d+/"
    ]
    names = [ "Scribd" ]
    _original = False
    media: dict = {}

    def _get_title(self):
        if self._title[-5:] == ", The":
            split = self._title.split(', ')
            if len(split) == 2:
                return f"{split[1]} {split[0]}"
        return self._title

    def get_cover(self) -> Optional[Cover]:
        # Downloading image from scribd
        raw_cover = self.get(self._cover)
        if raw_cover is None:
            return None
        if self._original:
            return Cover(raw_cover, "jpg")
        # Removing padding on the top and bottom if it is a normal book
        im = Image.open(io.BytesIO(raw_cover))
        width, height = im.size
        cropped = im.crop((0, int((height-width)/2), width, int(width+(height-width)/2)))
        cover = io.BytesIO()
        cropped.save(cover, format="jpeg")
        return Cover(cover.getvalue(), "jpg")

    def get_metadata(self) -> AudiobookMetadata:
        title = self._get_title()
        metadata = AudiobookMetadata(title)
        if not self._original:
            metadata.add_authors(self.meta["authors"])
            if self.meta["series"]:
                metadata.series = self.meta["series"][0]
        return metadata

    def _get_chapter_title(self, chapter):
        number = chapter["chapter_number"]
        if number == 0:
            return "Introduction"
        return f"Chapter {number}"

    def get_chapters(self) -> list[Chapter]:
        chapters = []
        if not self._original and "chapters" in self.meta:
            start_time = 0
            for chapter in self.meta["chapters"]:
                title = self._get_chapter_title(chapter)
                chapters.append(Chapter(start_time, title))
                start_time += chapter["duration"]
        return chapters

    def get_files(self) -> list[AudiobookFile]:
        if self._original:
            return self.get_stream_files(
                self._stream_url,
                headers={"Authorization": self._jwt},
            )
        else:
            files = []
            for i in self.media["playlist"]:
                chapter = i["chapter_number"]
                files.append(AudiobookFile(
                    url = i["url"],
                    title = f"Chapter {chapter}",
                    ext = "mp3",
                ))
            return files

    def prepare(self):
        try:
            # Change url to listen page if info page was used
            if self.match_num == 1:
                book_id = self.url.split("/")[4]
                self.url = f"https://www.scribd.com/listen/{book_id}"
            book_id = self.find_in_page(
                self.url,
                r'(?<=(external_id":"))(scribd_)?\d+',
                force_cookies = True
            )
        except DataNotPresent:
            raise UserNotAuthorized
        # The audiobook is a Scribd original if the id starts with "scribd_"
        if book_id[:7] == "scribd_":
            self._original_prepare(book_id)
        else:
            self._normal_prepare(book_id)

    def _normal_prepare(self, book_id: str):
        """Download necessary data for normal audiobooks on scribd"""
        try:
            headers = {'Session-Key': self.find_in_page(self.url, '(?<=(session_key":"))[^"]+')}
            user_id = self.find_in_page(self.url, r'(?<=(account_id":"scribd-))\d+')
            misc = self.get_json(
                f"https://api.findawayworld.com/v4/accounts/scribd-{user_id}/audiobooks/{book_id}",
                headers=headers,
            )
            self.meta = misc['audiobook']
            self._title = self.meta["title"]
            self._cover = self.meta["cover_url"]
            self.media = self.post_json(
                f"https://api.findawayworld.com/v4/audiobooks/{book_id}/playlists",
                headers=headers,
                json={
                    "license_id": misc['licenses'][0]['id']
                }
            )
            self.misc = misc
        except RequestError:
            raise UserNotAuthorized

    def _original_prepare(self, book_id: str):
        """Download necessary data for scribd originals"""
        self._original = True
        self._csrf = self.get_json(
            "https://www.scribd.com/csrf_token",
            headers={"href": self.url}
        )
        self._jwt = self.find_in_page(
            self.url,
            r'(?<=("jwt_token":"))[^"]+'
        )
        self._stream_url = f"https://audio.production.scribd.com/audiobooks/{book_id[7:]}/192kbps.m3u8"
        self._title = self.find_all_in_page(
            self.url,
            r'(?:("title":"))([^"]+)'
        )[1][1]
        self._cover = self.find_in_page(
            self.url,
            r'(?<=("cover_url":"))[^"]+'
        )
