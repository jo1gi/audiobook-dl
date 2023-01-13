from ..utils.source import Source
from ..utils.logging import debug
from ..utils.audiobook import AudiobookFile
from typing import List, Optional
import base64
from Crypto.Cipher import AES

class ChirpSource(Source):
    require_cookies = True
    match = [
        r"https://www.chirpbooks.com/player/\d+"
    ]

    headers = {
        "content-type": "application/json"
    }

    def get_tracks(self, book_id):
        response = self.post_json(
            f"https://www.chirpbooks.com/api/graphql",
            json = {
                "operationName": "fetchAudiobookTracks",
                "query": "query fetchAudiobookTracks($id:ID!){audiobook(id:$id){tracks{partNumber chapterNumber offsetFromBookStartMs durationMs displayName}}}",
                "variables": {
                    "id": book_id
                }
            },
            headers = self.headers,
        )
        return response["data"]["audiobook"]["tracks"]

    def get_title(self) -> str:
        return self.find_elem_in_page(self.url, "title")

    def get_metadata(self):
        return {}

    def get_cover(self) -> Optional[bytes]:
        cover_url = self.find_elem_in_page(self.url, "img.cover-image", data="src")
        return self.get(cover_url)

    def get_audio_url(self, track):
        url_resp = self.post_json(
            f"https://www.chirpbooks.com/api/graphql",
            json = {
                "operationName": "fetchAudiobookTrackUrl",
                "query": "query fetchAudiobookTrackUrl($id:ID!,$partNumber:Int!,$chapterNumber:Int!){audiobook(id:$id){track(partNumber:$partNumber,chapterNumber:$chapterNumber){webPlayerMediaUrl}}}",
                "variables": {
                    "id": self.book_id,
                    "chapterNumber": track["chapterNumber"],
                    "partNumber": track["partNumber"]
                }
            },
            headers = self.headers
        )
        webplayermediaurl = url_resp["data"]["audiobook"]["track"]["webPlayerMediaUrl"]
        ciphertext = base64.b64decode(webplayermediaurl)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.decrypt(ciphertext).decode("utf8")[:-1]

    def get_files(self) -> List[AudiobookFile]:
        files = []
        for track in self.tracks:
            pass
            files.append(AudiobookFile(
                url = self.get_audio_url(track),
                ext = "mp3",
                title = track["displayName"],
            ))
        return files

    def get_chapters(self):
        chapters = []
        start_time = 0
        for track in self.tracks:
            title = track["displayName"]
            chapters.append((start_time, title))
            start_time += track["durationMs"]
        return chapters

    def calc_iv(self):
        user_id = self.user_id
        padded_user_id = f"{'x'*(12-len(str(user_id)))}{user_id}"
        return base64.b64encode(bytes(padded_user_id, "UTF-8"))

    def before(self):
        self.book_id = int(self.find_elem_in_page(self.url, "div.user-audiobook", "data-audiobook-id"))
        debug(f"{self.book_id=}")
        self.user_id = int(self.find_in_page(self.url, r'"id":(\d+)', 1))
        debug(f"{self.user_id=}")
        self.tracks = self.get_tracks(self.book_id)
        self.iv = self.calc_iv()
        debug(f"{self.iv=}")
        self.key = bytes(self.find_elem_in_page(self.url, "div.user-audiobook", "data-dk"), "UTF-8")
        debug(f"{self.key=}")
