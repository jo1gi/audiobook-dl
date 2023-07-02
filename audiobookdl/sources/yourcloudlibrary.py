from .source import Source
from audiobookdl import AudiobookFile, logging, AudiobookMetadata, Cover, Audiobook
from audiobookdl.exceptions import UserNotAuthorized, RequestError

import requests.utils
import base64
from typing import List

class YourCloudLibrarySource(Source):
    match = [
        r"https?://ebook.yourcloudlibrary.com/library/[^/]+/AudioPlayer/.+"
    ]
    names = [ "YourCloudLibrary" ]
    _authentication_methods = [
        "cookies",
        "login"
    ]

    def download(self, url: str) -> Audiobook:
        fullfillment_token = self.download_fullfillment_token(url)
        book_info = self.download_book_info(url)
        library = self.extract_library_id(url)
        audioplayer = self.post_json(
            f"https://ebook.yourcloudlibrary.com/uisvc/{library}/AudioPlayer",
            data = {
                "url": f"{book_info['fullfillmentTokenUrl']}&token={fullfillment_token}"
            }
        )
        fulfillment_id = audioplayer["fulfillmentId"]
        account_id = audioplayer["accountId"]
        session_key = audioplayer["sessionKey"]
        headers = { "Session-Key": session_key }
        meta = self.get_json(
            f"https://api.findawayworld.com/v4/accounts/{account_id}/audiobooks/{fulfillment_id}",
            headers=headers
        )
        playlist = self.post_json(
            f"https://api.findawayworld.com/v4/audiobooks/{fulfillment_id}/playlists",
            json = {
                "license_id": audioplayer["licenseId"]
            },
            headers=headers
        )
        return Audiobook(
            session = self._session,
            files = self.get_files(playlist),
            metadata = self.get_metadata(book_info, meta),
            cover = self.download_cover(meta),
        )


    @staticmethod
    def get_files(playlist) -> List[AudiobookFile]:
        files = []
        for f in playlist["playlist"]:
            files.append(AudiobookFile(
                url = f["url"],
                ext = "mp3"
            ))
        return files


    def get_metadata(self, book_info, meta) -> AudiobookMetadata:
        title = book_info["Title"]
        metadata = AudiobookMetadata(title)
        if not meta is None:
            audiobook = meta["audiobook"]
            metadata.add_authors(audiobook["authors"])
            metadata.add_narrators(audiobook["narrators"])
            if audiobook["series"] is not None and len(audiobook["series"]) >= 1:
                metadata.series = audiobook["series"][0]
        return metadata


    def download_cover(self, meta) -> Cover:
        cover_url = meta['audiobook']['cover_url']
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")


    @staticmethod
    def extract_library_id(url: str) -> str:
        """
        Extract library id from url

        :param url: Url 
        :returns: Library id
        """
        return url.split("/")[-3]


    def download_fullfillment_token(self, url: str) -> str:
        """
        Download and extract fullfillment token

        :param url: Book url
        :returns: Fullfillment token
        """
        token_base64 = self.find_in_page(
            url,
            r"(?<=(\"Osi\":\"x-))[^\"]+",
            force_cookies = True,
        )
        if token_base64 is None:
            raise UserNotAuthorized
        token = base64.b64decode(token_base64).decode('utf8')
        logging.debug(f"{token=}")
        return token


    def download_book_info(self, url: str) -> dict:
        """
        Download metadata about book

        :param url: Book url
        :returns: Metadata about book
        """
        # Get list of borrowed books
        library = self.extract_library_id(url)
        borrowed = self.get_json(
            f"https://ebook.yourcloudlibrary.com/uisvc/{library}/Patron/Borrowed",
            force_cookies = True
        )
        if borrowed is None:
            raise UserNotAuthorized
        # Find the matching book in list of borrowed books
        url_id = url.split("/")[-1]
        book_info = None
        for i in borrowed:
            if i["Id"] == url_id:
                book_info = i
        if book_info is None:
            raise UserNotAuthorized
        return book_info


    def _login(self, url: str, username: str, password: str):
        library = self.extract_library_id(url)
        resp = self.post(
            f"https://ebook.yourcloudlibrary.com/uisvc/{library}/Patron/LoginPatron",
            data = {
                "UserId": username,
                "Password": password
            }
        )
        # TODO Validate authentication
        logging.debug(f"Authentication response {resp.decode('utf8')}")
