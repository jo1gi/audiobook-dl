with import <nixpkgs> {};

mkShell {
  buildInputs = [
    ffmpeg
    (python312.withPackages(ps: with ps; [
      mutagen
      requests
      rich
      lxml
      cssselect
      pillow
      m3u8
      pycryptodome
      importlib-resources
      platformdirs
      tomli
      attrs
      pycountry
      urllib3

      # Test
      pytest
      mypy
      types-requests
      types-setuptools

      # Build
      build
      setuptools
      twine
    ]))
  ];
}
