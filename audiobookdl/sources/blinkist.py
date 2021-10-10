from ..utils.service import Service


class BlinkistService(Service):
    require_cookies = True
    match = [
            r"https://www.blinkist.com/en/nc/reader/.+"
            ]

    def get_title(self):
        title = self.find_in_page(self.url, r"\"bookTitle\":\"[^\"]+")
        print(f"Title: {title}")
        return title
