FROM python:3.12-slim

# ffmpeg is needed for --combine, chapters and format conversion
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
# Editable install: package data (assets/) is picked up from git by
# setuptools-scm, which is unavailable here, so run straight from /app.
RUN pip install --no-cache-dir -e /app

# Config (audiobook-dl.toml, cookie files, source database) lives in
# /config/audiobook-dl; mount a host directory there to keep it between runs.
ENV XDG_CONFIG_HOME=/config
VOLUME ["/config"]

# Downloads land in the working directory; mount a host directory here.
WORKDIR /downloads
VOLUME ["/downloads"]

ENTRYPOINT ["audiobook-dl"]
CMD ["--help"]
