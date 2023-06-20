from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover, logging
from audiobookdl.exceptions import DataNotPresent
from typing import Any, List, Optional
import hashlib
import uuid
import platform
import datetime

APP_VERSION = "5.0.0"

def calculate_checksum(username: str, password: str, salt: str) -> str:
    return get_checksum(username + salt + password)


def calculate_password_checksum(password: str, salt: str) -> str:
    return get_checksum(password + salt)


def get_checksum(s: str) -> str:
    return hashlib.md5(s.encode()).digest().hex().zfill(32).upper()


def get_device_id() -> str:
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, "audiobook-dl"))


class NextorySource(Source):
    match = [
        r"https?://((www|catalog-\w\w).)?nextory.+",
    ]
    names = [ "Nextory" ]
    _authentication_methods = [
        "login",
    ]

    user_data: dict
    book_info: dict
    device_id: str

    def get_salt(self) -> str:
        url = "https://api.nextory.se/api/app/catalogue/7.5/salt"
        resp = self._session.get(url)
        if resp.status_code != 200:
            raise RuntimeError("Couldn't get salt from nextory.")
        return resp.json()["data"]["salt"]

    def _login(self, username: str, password: str):
        # Step one
        login_url = "https://api.nextory.se/api/app/user/7.5/login"
        self.device_id = get_device_id()
        headers = {
            "appid": "200",
            "model": "Personal Computer",
            "locale": "en_GB",
            "deviceid": self.device_id,
            "osinfo": platform.platform(),
            "version": "4.34.6",
            #"user-agent": "okhttp/4.9.3",
        }

        self._session.headers = headers
        salt = self.get_salt()
        files = {
            "username": (None, username),
            "password": (None, password),
            "checksum": (None, calculate_checksum(username, password, salt)),
        }
        resp = self._session.post(login_url, files=files)
        if resp.status_code != 200:
            raise PermissionError("Error in NextorySource login step one")

        login_info = resp.json()
        self._session.headers.update({'token': login_info["data"]["token"]})

        # Step two
        resp = self._session.get("https://api.nextory.se/api/app/user/7.5/accounts/list")
        if resp.status_code != 200:
            raise PermissionError("Error in NextorySource login step two")
        account_list = resp.json()

        # Step three
        params = {
            "loginkey": account_list["data"]["accounts"][0]["loginkey"],
            "checksum": calculate_password_checksum(account_list["data"]["accounts"][0]["loginkey"], salt)
        }

        resp = self._session.get(login_url, params=params)
        if resp.status_code != 200:
            raise PermissionError("Error in NextorySource login step three")

        account_info = resp.json()
        print(account_info)
        self._session.headers.update({'token': account_info["data"]["token"]})
        self._session.headers.update({'X-Login-Token': account_info["data"]["token"]})
        self._session.headers.update({'canary': account_info["data"]["canary"]})
        print(f'{account_info["data"]["canary"]}')
        exit()

        # Step four
        resp = self._session.get("https://api.nextory.se/api/app/library/7.5/active")
        if resp.status_code != 200:
            raise PermissionError("Error in NextorySource login step four")

        active = resp.json()

        self.user_data = {
            "login_info": login_info,
            "account_list": account_list,
            "account_info": account_info,
            "active": active,
        }
        self._session.headers.update({'apiver': "7.5"})


    def get_files(self) -> List[AudiobookFile]:
        return []
        # return [
        #     AudiobookFile(
        #         url=self.book_info["file"]["url"],
        #         headers=self._session.headers,
        #         ext="mp3"
        #     )
        # ]


    def get_metadata(self) -> AudiobookMetadata:
        title = self.book_metadata["title"]
        metadata = AudiobookMetadata(title)
        metadata.add_authors([author["name"] for author in self.book_metadata["authors"]])
        metadata.add_narrators([narrator["name"] for narrator in self.book_metadata["narrators"]])
        return metadata

    def get_chapters(self) -> List[Chapter]:
        # Nextory has no chapters...?
        return []


    def get_cover(self) -> Cover:
        cover_url = self.book_metadata["formats"][0]["img_url"].replace("{$width}", "640")
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")


    def prepare(self):
        # book_id = self.url.split("-")[-1].replace("/", "")
        book_id = "3122083"
        self.book_metadata = self._session.get(
            f"https://api.nextory.com/library/v1/products/{book_id}",
            headers = {
                "X-Device-Id": self.device_id,
                "X-Locale": "en_GB",
                "X-App-Version": APP_VERSION,
                "X-Model": "Phone Model",
                "X-Application-Id": "200",
                "X-Country-Code": "NO"
            }
        ).json()
        logging.debug(self.book_metadata)
        self.format_id = self.book_metadata["formats"][0]["identifier"]
        # self.file_data = self._session.get(
        #     f"https://api.nextory.com/reader/books/{self.format_id}/packages/audio",
        #     headers = {
        #         "X-Device-Id": self.device_id,
        #         "X-Locale": "en_GB",
        #         "X-App-Version": APP_VERSION,
        #         "X-Model": "Phone Model",
        #         "X-Application-Id": "200",
        #         "X-Country-Code": "NO"
        #     }
        # ).json()
        # logging.debug(self.file_data)
        profile_id = self.user_data["account_list"]["data"]["accounts"][0]["profileid"]
        resp = self._session.patch(
            f"https://api.nextory.com/reader/profiles/{profile_id}/books/{self.format_id}/position",
            json = {
                "position": {
                    "elapsed_time": 0,
                    "percentage": 0.0,
                    "reached_at": datetime.datetime.now().isoformat()
                }
            }
        )
        print(resp.content)
        # logging.debug(self.user_data["active"]["data"]["books"])
        logging.debug(self.user_data)
        exit()
        # for book in self.user_data["active"]["data"]["books"]:
        #     if str(book["id"]) == wanted_id:
        #         self.book_info = book
        #         logging.debug(self.book_info)
        #         return
        # raise PermissionError(f"Book with id {wanted_id} was not found in My Library.")
