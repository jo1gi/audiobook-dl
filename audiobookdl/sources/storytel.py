from .source import Source
from audiobookdl import AudiobookFile, Chapter, logging, AudiobookMetadata, Cover, Audiobook
from audiobookdl.exceptions import UserNotAuthorized, MissingBookAccess, DataNotPresent
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from typing import Any, List, Optional
from urllib3.util import parse_url
from urllib.parse import urlunparse


class StorytelSource(Source):
    match = [
        r"https?://(www.)?(storytel|mofibo).com/.+/books/.+",
    ]
    names = [ "Storytel", "Mofibo" ]
    _authentication_methods = [
        "login",
    ]

    @staticmethod
    def encrypt_password(password: str) -> str:
        """
        Encrypt password with predifined keys.
        This encrypted password is used for login.

        :param password: User defined password
        :returns: Encrypted password
        """
        # Thanks to https://github.com/javsanpar/storytel-tui
        key = b"VQZBJ6TD8M9WBUWT"
        iv = b"joiwef08u23j341a"
        msg = pad(password.encode(), AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = cipher.encrypt(msg)
        return cipher_text.hex()


    def _login(self, url: str, username: str, password: str):
        password = self.encrypt_password(password)
        self._session.headers.update({
            "content-type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0"
        })
        resp = self._session.get(
            f"https://www.storytel.com/api/login.action",
            params = {
                "m": 1,
                "uid": username,
                "pwd": password,
            }
        )
        if resp.status_code != 200:
            raise UserNotAuthorized
        user_data = resp.json()
        jwt = user_data["accountInfo"]["jwt"]
        self.single_signon_token = user_data["accountInfo"]["singleSignToken"]
        self._session.headers.update({"authorization": f"Bearer {jwt}"})



    def download(self, url: str) -> Audiobook:
        book_id = self.get_book_id(url)
        bookshelf = self.download_bookshelf()
        book_info = self.find_book_info(bookshelf, book_id)
        return Audiobook(
            session = self._session,
            files = self.get_files(book_info),
            metadata = self.get_metadata(book_info),
            cover = self.download_cover(book_info),
            chapters = self.get_chapters(book_info)
        )

    @staticmethod
    def get_book_id(url: str) -> str:
        """
        Find book id in url

        :param url: Url to book
        :returns: Id of book from url
        """
        parsed = parse_url(url)
        if parsed.path is None:
            raise DataNotPresent
        return parsed.path.split("-")[-1]

    def download_bookshelf(self):
        """Download bookshelf data"""
        return self._session.get(
            f"https://www.storytel.com/api/getBookShelf.action",
            params = {
                "token": self.single_signon_token
            }
        )


    @staticmethod
    def find_book_info(bookshelf, book_id: str):
        """
        Find book matching book_id in user bookshelf

        :param bookshelf: Users current listening boooks
        :param book_id: Id of book to download
        :returns: Book information
        """
        bookshelf = bookshelf.json()
        for book in bookshelf["books"]:
            if book["book"]["consumableId"] == book_id:
                return book
        raise MissingBookAccess




    def get_files(self, book_info) -> List[AudiobookFile]:
        aid = book_info["book"]["AId"]
        audio_url = f"https://www.storytel.com/mp3streamRangeReq?" \
            f"startposition=0&" \
            f"programId={aid}&" \
            f"token={self.single_signon_token}"
        return [
            AudiobookFile(
                url=audio_url,
                headers=self._session.headers,
                ext="mp3"
            )
        ]


    @staticmethod
    def get_metadata(book_info) -> AudiobookMetadata:
        title = book_info["book"]["name"]
        metadata = AudiobookMetadata(title)
        try:
            for author in book_info["book"]["authors"]:
                metadata.add_author(author["name"])
            for narrator in book_info["abook"]["narrators"]:
                metadata.add_narrator(narrator["name"])
            if "series" in book_info["book"]:
                if len(book_info["book"]["series"]) > 0:
                    metadata.series = book_info["book"]["series"][0]["name"]
            return metadata
        except:
            return metadata


    def download_audiobook_info(self, book_info):
        """Download information about the audiobook files"""
        consumable_id = book_info["book"]["consumableId"]
        url = f"https://api.storytel.net/playback-metadata/consumable/{consumable_id}"
        file_metadata = self._session.get(url).json()
        if not "formats" in file_metadata:
            raise DataNotPresent
        for format in file_metadata["formats"]:
            if format["type"] == "abook":
                return format
        raise DataNotPresent


    def get_chapters(self, book_info) -> List[Chapter]:
        chapters: List[Chapter] = []
        file_metadata = self.download_audiobook_info(book_info)
        if not "chapters" in file_metadata:
            return []
        start_time = 0
        for chapter in file_metadata["chapters"]:
            if "title" in chapter and chapter["title"] is not None:
                title = chapter["title"]
            else:
                title = f"Chapter {chapter['number']}"
            chapters.append(Chapter(start_time, title))
            start_time += chapter["durationInMilliseconds"]
        return chapters


    def download_cover(self, book_info) -> Cover:
        isbn = book_info["abook"]["isbn"]
        cover_url = f"https://www.storytel.com/images/{isbn}/640x640/cover.jpg"
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")
