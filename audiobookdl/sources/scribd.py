from .source import Source
from audiobookdl import AudiobookFile, Chapter, logging, AudiobookMetadata, Cover, Audiobook
from audiobookdl.exceptions import UserNotAuthorized, RequestError, DataNotPresent
from typing import List, Optional

import io
import re
from PIL import Image

class ScribdSource(Source):
    match = [
        r"https?://(www.)?scribd.com/listen/\d+",
        r"https?://(www.)?scribd.com/audiobook/\d+/"
    ]
    names = [ "Scribd" ]

    def download(self, url: str) -> Audiobook:
        try:
            # Change url to listen page if info page was used
            if re.match(self.match[1], url):
                url_id = url.split("/")[4]
                url = f"https://www.scribd.com/listen/{url_id}"
            book_id = self.download_book_id(url)
        except DataNotPresent:
            raise UserNotAuthorized
        if book_id[:7] == "scribd_":
            return self.download_scribd_original(book_id[:7], url)
        else:
            return self.download_normal_book(book_id, url)


    def download_scribd_original(self, book_id: str, url: str) -> Audiobook:
        """
        Download scribd original book

        :param book_id: Id of book
        :param url: Listening page for book
        :returns: Audiobook
        """
        csrf = self.get_json(
            "https://www.scribd.com/csrf_token",
            headers = { "href": url }
        )
        jwt = self.find_in_page(url, r'(?<=("jwt_token":"))[^"]+')
        stream_url = f"https://audio.production.scribd.com/audiobooks/{book_id}/192kbps.m3u8"
        title = self.find_in_page(url, r'(?:("title":"))([^"]+)')
        clean_title = self.clean_title(title)
        cover_url = self.find_in_page(url, r'(?<=("cover_url":"))[^"]+')
        return Audiobook(
            session = self._session,
            files = self.get_stream_files(stream_url, headers = { "Authorization": jwt }),
            # Does not have the normal metadata available
            metadata = AudiobookMetadata(title),
            cover = self.download_cover(cover_url, True),
        )


    def download_normal_book(self, book_id: str, url: str) -> Audiobook:
        """
        Download normal book from scribd

        :param book_id: Id of book
        :param url: Url of listening page
        :returns: Audiobook
        """
        try:
            headers = {'Session-Key': self.find_in_page(url, '(?<=(session_key":"))[^"]+')}
            user_id = self.find_in_page(url, r'(?<=(account_id":"scribd-))\d+')
            misc = self.get_json(
                f"https://api.findawayworld.com/v4/accounts/scribd-{user_id}/audiobooks/{book_id}",
                headers=headers,
            )
            book_info = misc["audiobook"]
            cover_url = book_info["cover_url"]
            media = self.post_json(
                f"https://api.findawayworld.com/v4/audiobooks/{book_id}/playlists",
                headers=headers,
                json={
                    "license_id": misc['licenses'][0]['id']
                }
            )
            return Audiobook(
                session = self._session,
                files = self.get_files(media),
                metadata = self.get_metadata(book_info),
                cover = self.download_cover(cover_url, original=False),
                chapters = self.get_chapters(book_info)
            )
        except RequestError:
            raise UserNotAuthorized


    def download_book_id(self, url: str) -> str:
        """
        Download and extract book id from listening page

        :param url: Url of listening page
        """
        return self.find_in_page(
            url,
            r'(?<=(external_id":"))(scribd_)?\d+',
            force_cookies = True
        )


    def download_cover(self, cover_url: str, original: bool) -> Optional[Cover]:
        """
        Download and clean cover

        :param cover_url: Url of cover
        :param original: True if the book is a Scribd Original
        :returns: Cover of book
        """
        # Downloading image from scribd
        raw_cover = self.get(cover_url)
        if raw_cover is None:
            return None
        if original:
            return Cover(raw_cover, "jpg")
        # Removing padding on the top and bottom if it is a normal book
        im = Image.open(io.BytesIO(raw_cover))
        width, height = im.size
        cropped = im.crop((0, int((height-width)/2), width, int(width+(height-width)/2)))
        cover = io.BytesIO()
        cropped.save(cover, format="jpeg")
        return Cover(cover.getvalue(), "jpg")


    @staticmethod
    def clean_title(title: str):
        """
        Move ', The' from the end to the beginning of the title

        :param title: Original title
        :returns: Fixed title
        """
        if title[-5:] == ", The":
            split = title.split(', ')
            if len(split) == 2:
                return f"{split[1]} {split[0]}"
        return title


    @staticmethod
    def get_metadata(book_info) -> AudiobookMetadata:
        title = book_info["title"]
        metadata = AudiobookMetadata(title)
        metadata.add_authors(book_info["authors"])
        if book_info["series"]:
            metadata.series = book_info["series"][0]
        return metadata


    @staticmethod
    def get_chapter_title(chapter):
        """Extract title for chapter"""
        number = chapter["chapter_number"]
        if number == 0:
            return "Introduction"
        return f"Chapter {number}"


    @staticmethod
    def get_chapters(book_info) -> List[Chapter]:
        chapters = []
        if "chapters" in book_info:
            start_time = 0
            for chapter in book_info["chapters"]:
                title = ScribdSource.get_chapter_title(chapter)
                chapters.append(Chapter(start_time, title))
                start_time += chapter["duration"]
        return chapters


    @staticmethod
    def get_files(media) -> List[AudiobookFile]:
        files = []
        for i in media["playlist"]:
            chapter = i["chapter_number"]
            files.append(AudiobookFile(
                url = i["url"],
                title = f"Chapter {chapter}",
                ext = "mp3",
            ))
        return files
