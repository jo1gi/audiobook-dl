{
  description = "audiobook-dl flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages.audiobook-dl = pkgs.callPackage ./default.nix { audiobook-dl-src = ./.; };
        packages.default = self.packages.${system}.audiobook-dl;
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            ffmpeg
            (python312.withPackages (
              ps: with ps; [
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

                # Test
                pytest
                mypy
                types-requests
                types-setuptools

                # Build
                build
                setuptools
                twine
              ]
            ))
          ];
        };
      }
    );
}
