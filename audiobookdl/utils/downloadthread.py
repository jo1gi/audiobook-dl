import threading
from . import metadata


class DownloadThread(threading.Thread):
    """Thread for downloading a file"""

    def __init__(self, session, path, url, metadata, progress, task):
        threading.Thread.__init__(self)
        self.session = session
        self.path = path
        self.metadata = metadata
        self.task = task
        self.progress = progress
        self.req = self.session.get(url, stream=True)
        self.length = int(self.req.headers['Content-length'])

    def run(self):
        with open(self.path, "wb") as f:
            for chunk in self.req.iter_content(chunk_size=1024):
                f.write(chunk)
                self.progress.update(self.task, advance=1024)
        if "title" in self.metadata:
            metadata.add_metadata(self.path, {"title": self.metadata["title"]})

    def get_length(self):
        return self.length
