# audiobook-dl
CLI tool for downloading audiobooks from online services.

## Supported Services
audiobook-dl currently supports downloading from the following services:
- audiobooks.com
- overdrive
- scribd

## Usage

### Cookies
audiobook-dl uses Netscape cookie files for authentication. I use
[this](https://github.com/rotemdan/ExportCookies) extension to export my cookies
from the browser.

### Installation
```shell
python3 setup.py install --user
```

### Downloading audiobooks
```shell
audiobook-dl -c <cookie file> <url>
```
