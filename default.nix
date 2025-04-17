{
  lib,
  python3,
  self,
}:
let
  inherit (lib) concatStringsSep substring;

  mkDate =
    longDate:
    (concatStringsSep "-" [
      (substring 0 4 longDate)
      (substring 4 2 longDate)
      (substring 6 2 longDate)
    ]);

  date = mkDate (self.lastModifiedDate or "19700101");
in

python3.pkgs.buildPythonApplication {
  pname = "audiobook-dl";
  version = "${date}_${self.shortRev or "dirty"}";
  pyproject = true;

  src = ./.;

  build-system = with python3.pkgs; [
    setuptools
    setuptools-scm
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
