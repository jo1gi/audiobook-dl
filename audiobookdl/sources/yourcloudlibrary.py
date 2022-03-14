from ..utils.source import Source
import requests.utils

class YourCloudLibrarySource(Source):
    requires_cookies = True
    match = [
            r"https?://ebook.yourcloudlibrary.com/library/[^/]+/AudioPlayer/.+"
    ]

    def get_title(self):
        return self.book_info["Title"]

    def get_files(self):
        files = []
        for n, f in enumerate(self.playlist["playlist"]):
            files.append({
                "url": f["url"],
                "part": n,
                "ext": "mp3",
            })
        return files

    def before(self):
        url_id = self.url.split("/")[-1]
        borrowed = self.get_json(
                "https://ebook.yourcloudlibrary.com/uisvc/Middlesex/Patron/Borrowed",
                cookies=requests.utils.dict_from_cookiejar(self._session.cookies))
        for i in borrowed:
            if i["Id"] == url_id:
                self.book_info = i
        audioplayer = self.post_json("https://ebook.yourcloudlibrary.com/uisvc/Middlesex/AudioPlayer",
                data={"url": f"{self.book_info['fulfillmentTokenUrl']}&token=a*nESEFL13XgGUVre*dAF*LA39s-LNhpySYSE8AMGwz@"})
        self.playlist = self.post_json(f"https://api.findawayworld.com/v4/audiobooks/{audioplayer['fulfillmentId']}/playlists",
                data='{"license_id":"' + audioplayer["licenseId"] + '"}',
                headers={"Session-Key": audioplayer["sessionKey"]})
