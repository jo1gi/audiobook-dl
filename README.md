# audiobook-dl
![GitHub release](https://img.shields.io/github/v/release/jo1gi/audiobook-dl)
![GitHub top language](https://img.shields.io/github/languages/top/jo1gi/audiobook-dl)
![License](https://img.shields.io/github/license/jo1gi/audiobook-dl)

CLI tool for downloading audiobooks from online sources.

## Maintainers
I'm currently looking for maintainers to support the different services. I
don't use all the services and have a hard time keeping up the support.

If you are interested, please contact me on:
- Matrix: jo1gi:matrix.org
- XMPP: verdantislet@movim.eu

## Supported Services
audiobook-dl currently supports downloading from the following sources:
- [audiobooks.com](https://audiobooks.com)
- [Blinkist](https://www.blinkist.com)
- [Chirp](https://www.chirpbooks.com/)
- [eReolen](https://ereolen.dk)
- [Everand (previously Scribd)](https://everand.com)
- [Librivox](https://librivox.org)
- [Nextory](https://nextory.com)
- [Overdrive](https://www.overdrive.com/)
- [Podimo](https://podimo.com)
- [Saxo](https://saxo.com)
- [Storytel](https://www.storytel.com/) / [Mofibo](https://mofibo.com)
- [YourCloudLibrary](https://www.yourcloudlibrary.com/)

[More info](./supported_sites.md)

## Installation
audiobook-dl can be installed from the repo itself or through pip.

To get the newest stable version with pip run:
```shell
pip install audiobook-dl
```

If you want to use the newest version (can be unstable) run:
```shell
pip install "git+https://github.com/jo1gi/audiobook-dl.git"
```
or
```shell
git clone https://github.com/jo1gi/audiobook-dl.git
cd audiobook-dl
python3 setup.py install
```

Some features require [ffmpeg](https://ffmpeg.org/) which can be installed
through most package managers or from [ffmpeg.org/download.html](https://ffmpeg.org/download.html).

## Authentication

### Cookies
audiobook-dl uses Netscape cookie files for authentication in most cases. I use
[this](https://github.com/rotemdan/ExportCookies) extension to export my cookies
from the browser.

Cookies can be placed in current dir as `cookies.txt` or be given with the
`--cookies` argument.

### Login
[Some sources](./supported_sites.md) support authentication through login with
username and password (and sometimes library). Use the `--username` and
`--password` arguments or enter them through an interactive prompt.

## Downloading audiobooks
```shell
audiobook-dl -c <cookie file> <url>
```
**Most sites require you to provide the listening page not not just the
information page**

## Arguments

| Argument                 | Value | Example |
|--------------------------|-------|---------|
| `urls`                   | One or more urls to download from | `audiobook-dl <url1> <url2>` |
| `-v`, `--version`        | Print version and exit | `audiobook-dl --version` |
| `-c`, `--cookies`        | Path to a Netscape cookie file | `audiobook-dl -c cookies.txt <url>` |
| `--combine`              | Combine all output files into a single file (requires ffmpeg) | `audiobook-dl --combine <url>` |
| `-o`, `--output`         | Output location/template (default: `{title}`) | `audiobook-dl -o "C:\Audiobooks\{title}" <url>` |
| `--remove-chars`         | List of characters that will be removed from output path | `audiobook-dl --remove-chars "[]()" <url>` |
| `-d`, `--debug`          | Print debug information | `audiobook-dl --debug <url>` |
| `-q`, `--quiet`          | Quiet mode | `audiobook-dl --quiet <url>` |
| `--print-output`         | Print the output path instead of downloading | `audiobook-dl --print-output <url>` |
| `--cover`                | Download only cover | `audiobook-dl --cover <url>` |
| `--no-chapters`          | Don't include chapters in output file | `audiobook-dl --no-chapters <url>` |
| `-f`, `--output-format`  | Output file format | `audiobook-dl -f mp3 <url>` |
| `--verbose-ffmpeg`       | Show ffmpeg output in terminal | `audiobook-dl --verbose-ffmpeg --combine <url>` |
| `--input-file`           | File with one url per line | `audiobook-dl --input-file urls.txt` |
| `--username`             | Username to source (required when using login) | `audiobook-dl --username "me@example.com" <url>` |
| `--password`             | Password to source (required when using login) | `audiobook-dl --password "secret" <url>` |
| `--library`              | Specific library on service (sometimes required when using login) | `audiobook-dl --library dk <url>` |
| `--skip-downloaded`      | Skip download if output file/folder already exists | `audiobook-dl --skip-downloaded <url>` |
| `--database_directory`   | Directory for source database/cache | `audiobook-dl --database_directory "C:\audiobook-db" <url>` |
| `--write-json-metadata`  | Write metadata in a separate `.json` file | `audiobook-dl --write-json-metadata <url>` |
| `--config`               | Alternative location of config file | `audiobook-dl --config "C:\path\audiobook-dl.toml" <url>` |

## Output
By default, audiobook-dl saves all audiobooks to `{title}` relative to the
current path. This can be changed with the `--output` argument. Path can be
customized by audiobook with the following fields:
- `title`
- `author`
- `narrator`
- `genre`
- `series`
- `series_order`
- `publisher`
- `release_date`
- `language`
- `isbn`
- `description`
- `scrape_url`
- `album` (default: `NA`)
- `artist` (default: `NA`)

Not all fields are available for all audiobooks.

The file extension can be changed with the `--output-format` argument.

### Output examples
```shell
audiobook-dl -o "{title}" <url>
audiobook-dl -o "C:\Audiobooks\{author}\{title}" <url>
audiobook-dl -o "C:\Audiobooks\{series}\{series_order} - {title}" <url>
```

## Configuration
audiobook-dl can be configured using a configuration file, which should be placed at:
- Windows: `C:\\Users\\$user\\AppData\\Local\\jo1gi\\audiobook-dl\\audiobook-dl.toml`
- Mac: `/Users/$user/Library/Application Support/audiobook-dl/audiobook-dl.toml`
- Linux `$XDG_CONFIG_DIR/audiobook-dl/audiobook-dl.toml`

### Authentications
Source credentials can be provided in the configuration file:
```toml
[sources.yourcloudlibrary]
username = "yourusername"
password = "supersecretpassword"
library = "hometown"
```

Cookie files can be specified in a similar way:
```toml
[sources.everand]
cookie_file = "./everand_cookies.txt"
```
Paths are relative to the configuration directory.

## Contributions
Issues, bug-reports, pull requests or ideas for features and improvements are
**very welcome**.
