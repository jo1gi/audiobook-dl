# audiobook-dl

CLI tool for downloading audiobooks from online sources.

## Supported Services
audiobook-dl currently supports downloading from the following sources:
- [audiobooks.com](https://audiobooks.com)
- [Blinkist](https://www.blinkist.com)
- [Chirp](https://www.chirpbooks.com/)
- [eReolen](https://ereolen.dk)
- [Everand (previously Scribd)](https://everand.com)
- [Librivox](https://librivox.org)
- [Nextory](https://nextory.com)
- [Overdrive / Libby](https://www.overdrive.com/)
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
pip install "git+https://github.com/manolozocco/audiobook-dl.git"
```
or
```shell
git clone https://github.com/manolozocco/audiobook-dl.git
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
`--cookie` argument.

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

| Argument          | Value                                                             |
|-------------------|-------------------------------------------------------------------|
| url               | The url of the page where you listen to the audiobook             |
| -c/--cookie       | Path to a Netscape cookie file                                    |
| --combine         | Combine all output files into a single file (requires ffmpeg)     |
| --cover           | Only download cover                                               |
| -d/--debug        | Print debug information                                           |
| -o/--output       | Output location                                                   |
| --remove-chars    | List of characters that will be removed from output path          |
| --no-chapters     | Don't include chapters in output file                             |
| --output-format   | Output file format                                                |
| --verbose-ffmpeg | Show ffmpeg output in terminal                                    |
| --username        | Username to source (Required when using login)                    |
| --password        | Password to source (Required when using login)                    |
| --library         | Specific library on service (Sometimes required when using login) |

## Output
By default, audiobook-dl saves all audiobooks to `{title}` relative to the
current path. This can be changed with the `--output` argument. Path can be
customized by audiobook with the following fields:
- `title`
- `author`
- `series`
- `narrator`

Not all fields are available for all audiobooks.

The file extension can be changed with the `--output-format` argument.

## Configuration
audiobook-dl can be configured using a configuration file, which should be placed at:
- Windows: `C:\\Users\\$user\\AppData\\Local\\manolozocco\\audiobook-dl\\audiobook-dl.toml`
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
