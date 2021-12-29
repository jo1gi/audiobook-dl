with import <nixpkgs> {};

mkShell {
  buildInputs = [
    ffmpeg
    (python3.withPackages(ps: with ps; [
      mutagen
      requests
      types-requests
      rich
      lxml
      pydub
      cssselect
      pillow
      mypy
      m3u8
      pycrypto
    ]))
  ];
}
