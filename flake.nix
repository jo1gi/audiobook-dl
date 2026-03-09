{
  description = "audiobook-dl flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        lib = pkgs.lib;

        mkDate =
          longDate:
          (lib.concatStringsSep "-" [
            (lib.substring 0 4 longDate)
            (lib.substring 4 2 longDate)
            (lib.substring 6 2 longDate)
          ]);

        date = mkDate (self.lastModifiedDate or "19700101");
        python = pkgs.python3;
      in
      {
        packages.default = self.packages.${system}.audiobook-dl;
        packages.audiobook-dl = python.pkgs.buildPythonApplication {
          pname = "audiobook-dl";
          version = "${date}_${self.shortRev or "dirty"}";
          pyproject = true;

          src = ./.;

          build-system = with python.pkgs; [
            setuptools
            setuptools-scm
          ];

          dependencies = with python.pkgs; [
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
            dateutils
          ];

          meta = {
            description = "Audiobook CLI downloader";
            homepage = "https://github.com/jo1gi/audiobook-dl";
            license = lib.licenses.gpl3Only;
            maintainers = with lib.maintainers; [ ];
            mainProgram = "audiobook-dl";
          };
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.ffmpeg
            (python.withPackages(ps: with ps; [
              mutagen
              requests
              rich
              lxml
              cssselect
              pillow
              m3u8
              pycryptodome
              importlib-resources
              appdirs
              tomli
              attrs
              pycountry
              urllib3
              dateutils

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

        };
      }
    );
}
