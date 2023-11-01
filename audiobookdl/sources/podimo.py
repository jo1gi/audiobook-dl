from .source import Source
from audiobookdl import logging
from audiobookdl.exceptions import NoSourceFound
from audiobookdl.utils import read_asset_file
from audiobookdl.utils.audiobook import Audiobook, AudiobookFile, AudiobookMetadata, Cover, Series, BookId, Result

import re
from typing import List
import requests
from requests import Response

class PodimoSource(Source[dict]):
    match = [
        "https://open.podimo.com/audiobook/[^/]+",
        "https://open.podimo.com/podcast/[^/]+",
    ]
    names = [ "Podimo" ]
    _authentication_methods = [
        "login"
    ]


    def _login(self, url: str, username: str, password: str) -> None:
        response = self.graphql_request(
            operation_name = "LoginResultsQuery",
            query = "login",
            variables = {
                "email": username,
                "password": password
            }
        )
        authorization_token = response.json()["data"]["tokenWithCredentials"]["accessToken"]
        logging.debug(f"{authorization_token=}")
        self._session.headers.update({"authorization": authorization_token})


    def graphql_request(self, operation_name: str, query: str, variables: dict) -> Response:
        """
        Make graphql request to Podimo

        :param operation_name: Name of operation
        :param query: File query is stored in
        :param variables: Variables for query
        :returns: Response from server
        """
        return self._session.post(
            "https://podimo.com/graphql",
            params = { "queryName": operation_name },
            json = {
                "operationName": operation_name,
                "query": read_asset_file(f"assets/sources/podimo/{query}.graphql"),
                "variables": variables
            }
        )


    @staticmethod
    def extract_id_from_url(url: str) -> str:
        """Extract audiobook id from url"""
        return url.split("/")[-1]


    def download(self, url: str) -> Result:
        if re.match(self.match[0], url):
            return self.download_audiobook(url)
        if re.match(self.match[1], url):
            return self.download_podcast(url)
        else:
            raise NoSourceFound


    def download_podcast(self, url: str) -> Series[dict]:
        """Download podcast info from Podimo"""
        podcast_id = self.extract_id_from_url(url)
        metadata = self.download_podcast_metadata(podcast_id)
        episodes = self.download_podcast_episode_ids(podcast_id)
        return Series(
            title = metadata["title"],
            books = episodes,
        )


    def download_podcast_metadata(self, podcast_id: str) -> dict:
        response = self.graphql_request(
            operation_name = "PodcastResultsQuery",
            query = "podcast",
            variables = {
                "id": podcast_id
            }
        )
        return response.json()["data"]["podcastById"]


    def download_podcast_episode_ids(self, podcast_id: str) -> List:
        response = self.graphql_request(
            operation_name = "PodcastEpisodesResultsQuery",
            query = "podcast_episodes",
            variables = {
                "limit": 1000,
                "offset": 0,
                "podcastId": podcast_id,
                "sorting": "PUBLISHED_ASCENDING"
            }
        )
        episodes = []
        for episode in response.json()["data"]["podcastEpisodes"]:
            episodes.append(BookId(episode))
        return episodes



    def download_from_id(self, episode_info: dict) -> Audiobook:
        episode_id = episode_info["id"]
        podcast_id = episode_info["podcastId"]
        return Audiobook(
            session = requests.Session(),
            files = self.get_podcast_file(episode_id, podcast_id),
            metadata = self.format_podcast_metadata(episode_info),
            cover = self.download_cover(episode_info["imageUrl"])
        )


    def get_podcast_file(self, episode_id: str, podcast_id: str) -> List[AudiobookFile]:
        """
        Download url of podcast episode

        :param episode_id: Internal id for episode
        :param podcast_id: Internal id for podcast
        :returns: Links to all podcast audio files
        """
        response = self.graphql_request(
            operation_name = "ShortLivedPodcastMediaUrlQuery",
            query = "podcast_episode_file",
            variables = {
                "episodeId": episode_id,
                "podcastId": podcast_id
            }
        )
        file_url = response.json()["data"]["podcastEpisodeStreamMediaById"]["url"]
        if "m3u8" in file_url:
            audio_url = file_url.replace("main.m3u8", "stream_audio_high/stream.m3u8")
            return self.get_stream_files(audio_url)
        else:
            return [ AudiobookFile( url = file_url, ext = "mp3" ) ]


    def format_podcast_metadata(self, episode_info) -> AudiobookMetadata:
        """
        Format unstructed json response as `AudiobookMetadata`

        :param episode_info: Json response from Podimo
        :returns: Important metadata as `AudiobookMetadata`
        """
        metadata = AudiobookMetadata(
            title = episode_info["title"],
            series = episode_info.get("podcastName"),
            description = episode_info.get("description"),
        )
        if episode_info["authorName"]:
            metadata.add_author(episode_info["authorName"])
        return metadata


    def download_audiobook(self, url: str) -> Audiobook:
        audiobook_id = self.extract_id_from_url(url)
        logging.debug(f"{audiobook_id=}")
        book_info = self.download_book_info(audiobook_id)
        metadata = self.format_audiobook_metadata(book_info)
        return Audiobook(
            # Will sometimes get a 'Authentication required' message if logged in
            session = requests.Session(),
            files = self.get_audiobook_files(audiobook_id),
            metadata = self.format_audiobook_metadata(book_info),
            cover = self.download_cover(book_info["coverImage"]["url"])
        )


    def get_audiobook_files(self, audiobook_id: str) -> List[AudiobookFile]:
        response = self._session.post(
            "https://open.podimo.com/graphql?queryName=ShortLivedAudiobookMediaUrlQuery",
            json = {
                "operationName": "ShortLivedAudiobookMediaUrlQuery",
                "query": read_asset_file("assets/sources/podimo/files.graphql"),
                "variables": {
                    "id": audiobook_id
                }
            }
        )
        audiobook_url = response.json()["data"]["audiobookAudioById"]["url"]
        return [AudiobookFile(url = audiobook_url, ext = "mp3")]


    def download_book_info(self, audiobook_id: str) -> dict:
        response = self._session.post(
            "https://open.podimo.com/graphql?queryName=AudiobookResultsQuery",
            json = {
                "operationName": "AudiobookResultsQuery",
                "query": read_asset_file("assets/sources/podimo/book_info.graphql"),
                "variables": {
                    "id": audiobook_id
                }
            }
        )
        return response.json()["data"]["audiobookById"]


    def format_audiobook_metadata(self, book_info) -> AudiobookMetadata:
        metadata = AudiobookMetadata(book_info["title"])
        for author in book_info["authors"]:
            metadata.add_author(author["name"])
        for narrator in book_info["narrators"]:
            metadata.add_narrator(narrator["name"])
        metadata.description = book_info.get("description")
        return metadata


    def download_cover(self, cover_url: str) -> Cover:
        # Will sometimes get a 'Authentication required' message if logged in
        response = requests.get(cover_url)
        return Cover(image = response.content, extension = "png")
