# audiobook-dl
![GitHub release](https://img.shields.io/github/v/release/jo1gi/audiobook-dl)
![GitHub top language](https://img.shields.io/github/languages/top/jo1gi/audiobook-dl)
![License](https://img.shields.io/github/license/jo1gi/audiobook-dl)

CLI tool for downloading audiobooks from online sources.

## Supported Services
audiobook-dl currently supports downloading from the following sources:
- [audiobooks.com](https://audiobooks.com)
- [Librivox](https://librivox.org)
- [Overdrive (Library service)](https://www.overdrive.com/)
- [Scribd](https://scribd.com)

## Installation
```shell
git clone https://github.com/jo1gi/audiobook-dl.git
cd audiobook-dl
python3 setup.py install
```

Some features require [ffmpeg](https://ffmpeg.org/) which can be installed
through most package managers or from [ffmpeg.org/download.html](https://ffmpeg.org/download.html).

## Cookies
audiobook-dl uses Netscape cookie files for authentication. I use
[this](https://github.com/rotemdan/ExportCookies) extension to export my cookies
from the browser.

## Downloading audiobooks
```shell
audiobook-dl -c <cookie file> <url>
```
**You have to use a link to the listening page and not just to the information
page**

## Arguments

| Argument    | Value                                                         |
|-------------|---------------------------------------------------------------|
| Url         | The url of the page where you listen to the audiobook         |
| -c/--cookie | Path to a Netscape cookie file                                |
| --combine   | Combine all output files into a single file (requires ffmpeg) |
