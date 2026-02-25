from .source import Source
from audiobookdl import  AudiobookFile, logging, utils, AudiobookMetadata, Cover, Audiobook
from audiobookdl.exceptions import RequestError, DataNotPresent, BookHasNoAudiobook

from typing import List
import re
import json
import pycountry
from urllib.parse import urlparse
import importlib
import requests

class EreolenSource(Source):
    _authentication_methods = [
        "cookies",
        "login"
    ]
    names = [ "eReolen" ]
    login_data = [ "username", "password" ]
    library_domains = utils.read_asset_file("assets/sources/ereolen/libraries.txt").split("\n")
    match = [
        rf"https://(www.)?({"|".join(library_domains)})/work/work-of:.+",
    ]

    def _login(self, url: str, username: str, password: str):
        hostname = urlparse(url).hostname
        login_page_url = f"https://{hostname}/login"
        login_path = self.find_elem_in_page(login_page_url, "#borchk-login-form", "action")
        library_id = self.find_elem_in_page(login_page_url, "#libraryid-input", "value")
        library_name = self.find_elem_in_page(login_page_url, "#libraryname-input", "value")
        logging.debug(f"{library_name=} {library_id=}")
        response = self._session.post(
            f"https://login.bib.dk{login_path}",
            headers = { "Content-Type": "application/x-www-form-urlencoded" },
            data = {
                "libraryName": library_name,
                "agency": library_id,
                "loginBibDkUserId": username,
                "pincode": password
            },
            allow_redirects = True,
            timeout = 20.,
        )
        user_token = self.find_in_page(
            f"https://{hostname}/dpl-react/user-tokens",
            '"user", "(.+)"',
            1
        )
        self._session.headers.update({
            "Authorization": f"Bearer {user_token}"
        })
        logging.debug(f"{user_token=}")


    def download(self, url: str) -> Audiobook:
        work_id = urlparse(url).path.split("/")[-1]
        logging.debug(f"{work_id=}")

        # Extract api path
        api_path_segment = self.find_in_page(url, 'data-fbi-base-url="https://fbi-api.dbc.dk/([^/]+)/graphql"', 1)
        logging.debug(f"{api_path_segment=}")

        # Fetch metadata
        metadata = self.post_json(
            f"https://fbi-api.dbc.dk/{api_path_segment}/graphql",
            json = {
                "query": utils.read_asset_file("assets/sources/ereolen/metadata_query.graphql"),
                "variables": {
                    "wid": work_id
                }
            },
        )
        if metadata is None:
            raise RequestError
        metadata = metadata["data"]["work"]

        # Extract book id
        book_id: str | None = None
        for manifestation in metadata["manifestations"]["all"]:
            if manifestation["materialTypes"][0]["materialTypeSpecific"]["display"] == "lydbog (online)":
                book_id = manifestation["identifiers"][0]["value"]
        if book_id is None:
            raise BookHasNoAudiobook
        logging.debug(f"{book_id=}")

        # Fetch loans
        loans = self.get_json("https://pubhub-openplatform.dbc.dk/v1/user/loans?")
        logging.debug(f"{loans=}")
        order_id: str | None = None
        for loan in loans["loans"]:
            if loan["libraryBook"]["identifier"] == book_id:
                order_id = loan["orderId"]

        if order_id is None:
            raise DataNotPresent

        return Audiobook(
            session = requests.Session(),
            files = self.get_files(order_id),
            metadata = AudiobookMetadata(
                title = metadata["titles"]["full"][0],
                authors = [author["display"] for author in metadata["creators"]],
                scrape_url = url,
            ),
            # cover = self.get_cover(meta),
        )


    def get_files(self, order_id: str) -> List[AudiobookFile]:
        return self.get_stream_files(
            f"https://audio.api.streaming.pubhub.dk/v1/stream/hls/{order_id}/playlist.m3u8",
            extension = "ts"
        )
