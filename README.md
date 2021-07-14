# audiobook-dl
![GitHub release](https://img.shields.io/github/v/release/jo1gi/audiobook-dl)
![GitHub top language](https://img.shields.io/github/languages/top/jo1gi/audiobook-dl)
![License](https://img.shields.io/github/license/jo1gi/audiobook-dl)

CLI tool for downloading audiobooks from online services.

## Supported Services
audiobook-dl currently supports downloading from the following services:
- audiobooks.com
- overdrive
- scribd

## Installation
```shell
python3 setup.py install
```

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

| Argument    | Value                                                 |
|-------------|-------------------------------------------------------|
| Url         | The url of the page where you listen to the audiobook |
| -c/--cookie | Path to a Netscape cookie file                        |
| --combine   | Combine all output files into a single file           |
