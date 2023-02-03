from .source import Source
from audiobookdl import AudiobookFile
from audiobookdl.exceptions import UserNotAuthorized, MissingBookAccess
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from typing import Any


class StorytelSource(Source):
    match = [
        r"https?://(www.)?(storytel|mofibo).com/.+/books/.+",
    ]
    names = [ "Storytel", "Mofibo" ]
    _authentication_methods = [
        "login",
    ]

    user_data: dict
    book_info: dict

    @staticmethod
    def encrypt_password(password: str) -> str:
        # Thanks to https://github.com/javsanpar/storytel-tui
        key = b"VQZBJ6TD8M9WBUWT"
        iv = b"joiwef08u23j341a"
        msg = pad(password.encode(), AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = cipher.encrypt(msg)
        return cipher_text.hex()

    def _login(self, username: str, password: str):
        password = self.encrypt_password(password)
        url = f"https://www.storytel.com/api/login.action?m=1&uid={username}&pwd={password}"
        self._session.headers.update({
            "content-type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0"
        })
        resp = self._session.get(url)
        if resp.status_code != 200:
            raise UserNotAuthorized
        self._session.headers.update({"authorization": f"Bearer {resp.json()['accountInfo']['jwt']}"})
        self.user_data = resp.json()

    def get_title(self) -> str:
        return self.book_info["book"]["name"]

    def get_files(self) -> list[AudiobookFile]:
        aid = self.book_info["book"]["AId"]
        url = f"https://www.storytel.com/mp3streamRangeReq?startposition=0&programId={aid}" \
              f"&token={self.user_data['accountInfo']['singleSignToken']}"
        return [AudiobookFile(url=url, headers=self._session.headers, ext="mp3")]

    def get_metadata(self) -> dict[str,Any]:
        try:
            metadata = {"authors": [a["name"] for a in self.book_info["book"]["authors"]],
                        "narrators": [a["name"] for a in self.book_info["abook"]["narrators"]]}
            if "series" in self.book_info["book"]:
                if len(self.book_info["book"]["series"]) > 0:
                    metadata["series"] = self.book_info["book"]["series"][0]["name"]
            return metadata
        except:
            return {}

    def get_chapters(self) -> list[tuple[int, str]] | None:
        url = f"https://api.storytel.net/playback-metadata/consumable/{self.book_info['book']['consumableId']}"
        try:
            chapters: list[tuple[int, str]] = []
            storytel_metadata = self._session.get(url).json()
            if "formats" in storytel_metadata and len(storytel_metadata["formats"]) > 0:
                f = storytel_metadata["formats"][0]
                if "chapters" in f and len(f["chapters"]) > 0:
                    start_time = 0
                    for c in f["chapters"]:
                        chapters.append((start_time, c["title"] if c["title"] else f"Chapter {c['number']}"))
                        start_time += c["durationInMilliseconds"]
            return chapters if len(chapters) > 0 else None
        except:
            return None

    def get_cover(self) -> bytes | None:
        url = f"https://www.storytel.com/images/{self.book_info['abook']['isbn']}/640x640/cover.jpg"
        return self.get(url)

    def before(self):
        wanted_id = self.url.split("-")[-1]
        bookshelf_url = f"https://www.storytel.com/api/getBookShelf.action" \
                        f"?token={self.user_data['accountInfo']['singleSignToken']}"
        self.user_data["bookshelf"] = self._session.get(bookshelf_url).json()
        for book in self.user_data["bookshelf"]["books"]:
            if book["book"]["consumableId"] == wanted_id:
                self.book_info = book
                return
        raise MissingBookAccess
