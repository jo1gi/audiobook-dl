from .source import Source
from audiobookdl import AudiobookFile, Chapter, logging, AudiobookMetadata, Cover, Audiobook
from audiobookdl.exceptions import DataNotPresent, GenericAudiobookDLException

from typing import Any, List, Optional
import os
import pycountry

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None

GRAPHQL_URL = "https://www.chirpbooks.com/api/graphql"

# Chirp sits behind Cloudflare, which fingerprints the TLS ClientHello (JA3) and
# serves a "Just a moment..." challenge (HTTP 403) to anything that doesn't look
# like a real browser. This happens even when a valid `cf_clearance` cookie is
# present, because that cookie is bound to the exact TLS/browser fingerprint that
# originally solved the challenge. Plain `requests` (and the base `Source`
# session) therefore cannot get through. curl_cffi reproduces a real browser's
# TLS fingerprint, which lets the exported `cf_clearance` cookie be accepted.
# The impersonation target must match the browser the cookies came from; Chrome
# is the common case (Firefox/Edge fingerprints are rejected with these cookies).
# Deliberately the unversioned "chrome" alias so curl_cffi tracks a current
# Chrome fingerprint across upgrades; pin a specific version (e.g. "chrome124")
# only if Cloudflare starts rejecting the rolling alias.
CLOUDFLARE_IMPERSONATE = "chrome"

# The id in a `/player/<id>` URL is the user's library-item id, not the
# audiobook id the GraphQL API expects. The player page exposes the real
# audiobook id as `data-audiobook-id` on `div.user-audiobook`.
AUDIOBOOK_ID_SELECTOR = "div.user-audiobook"

# A single GraphQL request returns metadata, cover and every track, each with a
# ready-to-download signed `mediaUrl`. The old flow decrypted a per-track
# `webPlayerMediaUrl` with the page's AES key (`data-dk`); `mediaUrl` is a plain
# signed audio URL, so the key, IV and decryption are no longer needed.
AUDIOBOOK_QUERY = (
    "query fetchAudiobook($id:ID!){"
    "audiobook(id:$id){"
    "displayTitle displayAuthors displayNarrators publisher language coverUrl "
    "tracks{partNumber chapterNumber displayName durationMs mediaUrl} "
    "supplements{url}"
    "}}"
)


class ChirpSource(Source):
    match = [
        r"https?://(?:www\.)?chirpbooks\.com/player/\d+"
    ]
    names = [ "Chirp" ]
    headers = {
        "content-type": "application/json"
    }


    def create_session(self, options: Any):
        if curl_requests is None:
            raise GenericAudiobookDLException(
                "Chirp requires the 'curl_cffi' package to get past Cloudflare. "
                "Install it with 'pip install curl_cffi'."
            )
        # Impersonate a browser's TLS fingerprint so Cloudflare accepts the
        # exported `cf_clearance` cookie (see CLOUDFLARE_IMPERSONATE above).
        return curl_requests.Session(impersonate=CLOUDFLARE_IMPERSONATE)


    def download(self, url: str) -> Audiobook:
        # Resolve the player/library id in the URL to the real audiobook id,
        # which the player page carries in `data-audiobook-id`.
        book_id = int(self.find_elem_in_page(url, AUDIOBOOK_ID_SELECTOR, "data-audiobook-id"))
        audiobook = self._fetch_audiobook(book_id)
        tracks = audiobook["tracks"]
        return Audiobook(
            session = self._session,
            files = self.get_files(tracks),
            metadata = self.get_metadata(audiobook),
            cover = self.get_cover(audiobook),
            chapters = self.get_chapters(tracks),
            supplements = self.get_supplements(audiobook)
        )


    def _fetch_audiobook(self, book_id: int) -> dict:
        response = self.post_json(
            GRAPHQL_URL,
            json = {
                "operationName": "fetchAudiobook",
                "query": AUDIOBOOK_QUERY,
                "variables": { "id": book_id }
            },
            headers = self.headers
        )
        if response.get("errors"):
            logging.debug(f"Chirp graphql returned errors: {response['errors']}")
        audiobook = (response.get("data") or {}).get("audiobook")
        if not audiobook:
            logging.debug(f"Unexpected Chirp graphql response: {response}")
            raise DataNotPresent
        return audiobook


    def get_metadata(self, audiobook: dict) -> AudiobookMetadata:
        metadata = AudiobookMetadata(audiobook["displayTitle"])
        # Chirp returns authors/narrators as single comma-joined display strings
        metadata.add_authors(self._split_names(audiobook.get("displayAuthors")))
        metadata.add_narrators(self._split_names(audiobook.get("displayNarrators")))
        if audiobook.get("publisher"):
            metadata.publisher = audiobook["publisher"]
        if audiobook.get("language"):
            language = pycountry.languages.get(name=audiobook["language"])
            if language is not None:
                metadata.language = language
            else:
                logging.debug(f"Could not map Chirp language {audiobook['language']!r} to pycountry")
        return metadata


    @staticmethod
    def _split_names(value: Optional[str]) -> List[str]:
        if not value:
            return []
        return [name.strip() for name in value.split(",") if name.strip()]


    def get_cover(self, audiobook: dict) -> Optional[Cover]:
        cover_url = audiobook.get("coverUrl")
        if not cover_url:
            return None
        # Covers are served through Cloudinary; the default `f_auto` transform
        # returns WebP. Force JPEG for the widest tagging compatibility.
        cover_url = cover_url.replace("f_auto", "f_jpg")
        return Cover(self.get(cover_url), "jpg")


    def get_files(self, tracks) -> List[AudiobookFile]:
        files = []
        for track in tracks:
            files.append(AudiobookFile(
                url = track["mediaUrl"],
                ext = "m4a",
                title = track["displayName"],
            ))
        return files


    def get_supplements(self, audiobook: dict) -> List[AudiobookFile]:
        """Bonus material (e.g. a PDF booklet) bundled with the audiobook"""
        supplements = []
        for supplement in audiobook.get("supplements") or []:
            url = supplement.get("url")
            if not url:
                continue
            # Derive the extension from the URL path (dropping any query string)
            ext = os.path.splitext(url.split("?")[0])[1].lstrip(".").lower() or "pdf"
            supplements.append(AudiobookFile(url=url, ext=ext))
        return supplements


    def get_chapters(self, tracks) -> List[Chapter]:
        chapters = []
        start_time = 0
        for track in tracks:
            chapters.append(Chapter(start_time, track["displayName"]))
            start_time += track["durationMs"]
        return chapters
