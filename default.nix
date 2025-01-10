{
  lib,
  python3,
  audiobook-dl-src,
}:

python3.pkgs.buildPythonApplication rec {
  pname = "audiobook-dl";
  version = "unstable-2024-10-24";
  pyproject = true;

  src = audiobook-dl-src;

  build-system = [
    python3.pkgs.setuptools
    python3.pkgs.setuptools-scm
  ];

  dependencies = with python3.pkgs; [
    appdirs
    attrs
    cssselect
    importlib-resources
    lxml
    m3u8
    mutagen
    pillow
    pycountry
    pycryptodome
    requests
    rich
    tomli
    urllib3
  ];

  meta = {
    description = "Audiobook CLI downloader";
    homepage = "https://github.com/jo1gi/audiobook-dl";
    license = lib.licenses.gpl3Only;
    maintainers = with lib.maintainers; [ ];
    mainProgram = "audiobook-dl";
  };
}
