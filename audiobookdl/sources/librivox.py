from ..utils.source import Source


class LibrivoxSource(Source):
    require_cookies = False
    match = [
        r"https?://librivox.org/.+"
    ]

    def get_title(self):
        return self.find_elem_in_page(self.url, ".content-wrap h1")

    def get_cover(self):
        return self.get(self.find_elem_in_page(
            self.url,
            ".book-page-book-cover img",
            data="src"))

    def get_files(self):
        parts = self.find_elems_in_page(self.url,
                                        ".chapter-download .chapter-name")
        files = []
        for n, part in enumerate(parts):
            files.append({
                "title": part.text,
                "url": part.get("href"),
                "part": n,
                "ext": "mp3",
            })
        return files
