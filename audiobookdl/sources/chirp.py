from .source import Source
from audiobookdl import AudiobookFile, Chapter, logging, AudiobookMetadata, Cover, Audiobook

from typing import List, Optional, Tuple
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


    def download(self, url: str) -> Audiobook:
        book_id = int(self.find_elem_in_page(url, "div.user-audiobook", "data-audiobook-id"))
        user_id = int(self.find_in_page(url, r'"id":(\d+)', 1))
        tracks = self._get_tracks(book_id)
        key, iv = self._create_key(url, user_id)
        return Audiobook(
            session = self._session,
            files = self.get_files(book_id, key, iv, tracks),
            metadata = self.get_metadata(url),
            cover = self.get_cover(url),
            chapters = self.get_chapters(tracks)
        )


    def get_metadata(self, url: str) -> AudiobookMetadata:
        title = self.find_elem_in_page(url, "title")
        metadata = AudiobookMetadata(title)
        for credit in self.find_elems_in_page(url, ".credit"):
            text = credit.text
            if text.startswith("Written by"):
                metadata.add_author(text[11:])
            elif text.startswith("Narrated by"):
                metadata.add_narrator(text[12:])
        return metadata


    def get_cover(self, url: str) -> Cover:
        cover_url = self.find_elem_in_page(url, "img.cover-image", data="src")
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")


    def get_audio_url(self, book_id: int, key: bytes, iv: bytes, track):
        url_resp = self.post_json(
            f"https://www.chirpbooks.com/api/graphql",
            json = {
                "operationName": "fetchAudiobookTrackUrl",
                "query": "query fetchAudiobookTrackUrl($id:ID!,$partNumber:Int!,$chapterNumber:Int!){audiobook(id:$id){track(partNumber:$partNumber,chapterNumber:$chapterNumber){webPlayerMediaUrl}}}",
                "variables": {
                    "id": book_id,
                    "chapterNumber": track["chapterNumber"],
                    "partNumber": track["partNumber"]
                }
            },
            headers = self.headers
        )
        webplayermediaurl = url_resp["data"]["audiobook"]["track"]["webPlayerMediaUrl"]
        ciphertext = base64.b64decode(webplayermediaurl)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.decrypt(ciphertext).decode("utf8")[:-1]


    def get_files(self, book_id: int, key: bytes, iv: bytes, tracks) -> List[AudiobookFile]:
        files = []
        for track in tracks:
            files.append(AudiobookFile(
                url = self.get_audio_url(book_id, key, iv, track),
                ext = "mp3",
                title = track["displayName"],
            ))
        return files


    def get_chapters(self, tracks) -> List[Chapter]:
        chapters = []
        start_time = 0
        for track in tracks:
            title = track["displayName"]
            chapters.append(Chapter(start_time, title))
            start_time += track["durationMs"]
        return chapters


    def _create_key(self, url: str, user_id: int) -> Tuple[bytes, bytes]:
        """Creates key and iv to decrypt audio url"""
        key = bytes(self.find_elem_in_page(url, "div.user-audiobook", "data-dk"), "UTF-8")
        # Creates IV based on `user_id`
        padding = 'x'*(12-len(str(user_id)))
        padded_user_id = f"{padding}{user_id}"
        iv = base64.b64encode(bytes(padded_user_id, "UTF-8"))
        return key, iv


    def _get_tracks(self, book_id: int):
        response = self.post_json(
            f"https://www.chirpbooks.com/api/graphql",
            json = {
                "operationName": "fetchAudiobookTracks",
                "query": "query fetchAudiobookTracks($id:ID!){audiobook(id:$id){tracks{partNumber chapterNumber offsetFromBookStartMs durationMs displayName}}}",
                "variables": {
                    "id": book_id
                }
            },
            headers = self.headers
        )
        return response["data"]["audiobook"]["tracks"]
