from ..utils.service import Service
import re, json, rich

class OverdriveService(Service):
    require_cookies = True
    match = [
        r"https://.+\.listen\.overdrive\.com"
    ]

    def before(self):
        raw = self.find_in_page(self.url, 'window.bData = {.+;')[15:][:-1]
        self.meta = json.loads(raw)
        self.toc = []
        for part in self.meta["nav"]["toc"]:
            if "contents" in part:
                for i in range(len(part["contents"])):
                    self.toc.append(part["title"])
            else:
                self.toc.append(part["title"])

    def get_title(self):
        return self.meta["title"]["main"]

    def get_files(self):
        prefix = re.search(self.match[0], self.url).group(0)
        files = []
        for num, part in enumerate(self.meta["spine"]):
            files.append({
                "url": f"{prefix}/{part['path']}",
                "title": self.toc[num],
                "part": num+1,
                "ext": "mp3"
            })
        return files
