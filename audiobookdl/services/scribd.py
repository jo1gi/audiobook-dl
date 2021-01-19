from ..utils.service import Service
from PIL import Image
import time

class ScribdService(Service):
    match = [
        "https?://www.scribd.com/listen/\d+"
    ]
    require_cookies = True

    def get_title(self):
        split = self.meta['title'].split(', ')
        if len(split) == 1:
            return split[0]
        if len(split) == 2:
            return f"{split[1]} {split[0]}"

    def _fix_cover(self):
        image = f"{self.title}/Cover.jpg"
        im = Image.open(image)
        width, height = im.size
        cropped = im.crop((0, (height-width)/2, width, width+(height-width)/2))
        cropped.save(image)
        time.sleep(2)

    def get_files(self):
        files = []
        # Cover image
        files.append({
            "name": "Cover.jpg",
            "url": self.meta["cover_url"]
        })
        # Audio files
        for i in self.media["playlist"]:
            chapter = i["chapter_number"]
            chapter_str = "0"*(3-len(str(chapter)))+str(chapter)
            files.append({
                "url": i["url"],
                "title": "Chapter {chapter}",
                "part": chapter_str,
                "ext": "mp3"
            })
        return files

    def before(self, *args):
        user_id = self.find_in_page(self.url, '(?<=(account_id":"scribd-))\d+')
        book_id = self.find_in_page(self.url, '(?<=(external_id":"))\d+')
        headers =  {
            'Session-Key': self.find_in_page(self.url, '(?<=(session_key":"))[^"]+')
        }
        misc = self.get_json(
            f"https://api.findawayworld.com/v4/accounts/scribd-{user_id}/audiobooks/{book_id}",
            headers = headers,
        )
        self.meta = misc['audiobook']
        self.media = self.post_json(
            f"https://api.findawayworld.com/v4/audiobooks/{book_id}/playlists",
            headers=headers,
            json={
                "license_id": misc['licenses'][0]['id']
            }
        )
