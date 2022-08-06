import threading
from . import metadata
from Crypto.Cipher import AES
from .logging import debug


class DownloadThread(threading.Thread):
    """Thread for downloading a file"""

    def __init__(self, session, path, url, metadata, progress, task):
        threading.Thread.__init__(self)
        self.session = session
        self.path = path
        self.metadata = metadata
        self.task = task
        self.progress = progress
        headers = {} if "headers" not in metadata else metadata["headers"]
        self.req = self.session.get(url, headers=headers, stream=True)
        debug(f"{self.req.headers=}")
        self.length = int(self.req.headers['Content-length'])

    def run(self):
        with open(self.path, "wb") as f:
            for chunk in self.req.iter_content(chunk_size=1024):
                f.write(chunk)
                self.progress.update(self.task, advance=1024)
        if "encryption_key" in self.metadata:
            with open(self.path, "rb") as f:
                cipher = AES.new(
                    self.metadata["encryption_key"],
                    AES.MODE_CBC,
                    self.metadata["iv"]
                )
                decrypted = cipher.decrypt(f.read())
            with open(self.path, "wb") as f:
                f.write(decrypted)
        metadata.add_metadata(self.path, self.metadata)

    def get_length(self):
        return self.length
