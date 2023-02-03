with import <nixpkgs> {};

mkShell {
  buildInputs = [
    ffmpeg
    (python3.withPackages(ps: with ps; [
      mutagen
      requests
      rich
      lxml
      cssselect
      pillow
      m3u8
      pycryptodome
      setuptools

      # Test
      pytest
      mypy
      types-requests
      types-setuptools

      # Build
      build
      twine
    ]))
  ];
}
