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
python3 setup.py install
```

### Downloading audiobooks
```shell
audiobook-dl -c <cookie file> <url>
```

### Arguments

| Argument    | Value                                                 |
|-------------|-------------------------------------------------------|
| Url         | The url of the page where you listen to the audiobook |
| -c/--cookie | Path to a Netscape cookie file                        |
| --combine   | Combine the give output files into a single file      |
