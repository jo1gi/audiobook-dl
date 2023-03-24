from .source import Source
from audiobookdl import AudiobookFile, Chapter, logging, AudiobookMetadata, Cover

from typing import Optional
import base64
from Crypto.Cipher import AES

LOGIN_URL = "https://www.chirpbooks.com/users/sign_in"

class ChirpSource(Source):
    match = [
        r"https://www.chirpbooks.com/player/\d+"
    ]

    names = [ "Chirp" ]

    headers = {
        "content-type": "application/json"
    }

    def _get_tracks(self, book_id):
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


    def get_metadata(self) -> AudiobookMetadata:
        title = self.find_elem_in_page(self.url, "title")
        metadata = AudiobookMetadata(title)
        for credit in self.find_elems_in_page(self.url, ".credit"):
            text = credit.text
            if text.startswith("Written by"):
                metadata.add_author(text[11:])
            elif text.startswith("Narrated by"):
                metadata.add_narrator(text[12:])
        return metadata


    def get_cover(self) -> Cover:
        cover_url = self.find_elem_in_page(self.url, "img.cover-image", data="src")
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")


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


    def get_files(self) -> list[AudiobookFile]:
        files = []
        for track in self.tracks:
            files.append(AudiobookFile(
                url = self.get_audio_url(track),
                ext = "mp3",
                title = track["displayName"],
            ))
        return files


    def get_chapters(self) -> list[Chapter]:
        chapters = []
        start_time = 0
        for track in self.tracks:
            title = track["displayName"]
            chapters.append(Chapter(start_time, title))
            start_time += track["durationMs"]
        return chapters


    def _calc_iv(self):
        """Creates IV based on `user_id` to decrypt audio url"""
        padding = 'x'*(12-len(str(self.user_id)))
        padded_user_id = f"{padding}{self.user_id}"
        return base64.b64encode(bytes(padded_user_id, "UTF-8"))


    def prepare(self):
        self.book_id = int(self.find_elem_in_page(self.url, "div.user-audiobook", "data-audiobook-id"))
        logging.debug(f"{self.book_id=}")
        self.user_id = int(self.find_in_page(self.url, r'"id":(\d+)', 1))
        logging.debug(f"{self.user_id=}")
        self.tracks = self._get_tracks(self.book_id)
        self.iv = self._calc_iv()
        logging.debug(f"{self.iv=}")
        self.key = bytes(self.find_elem_in_page(self.url, "div.user-audiobook", "data-dk"), "UTF-8")
        logging.debug(f"{self.key=}")
