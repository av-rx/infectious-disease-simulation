{
  description = "A flake for running infectious_disease_simulation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixpkgs-unstable";
  };

  outputs = { nixpkgs, ... }: {
    defaultPackage.x86_64-linux = 
      with import nixpkgs { system = "x86_64-linux"; };
        pkgs.python3Packages.buildPythonPackage {
          pname = "infectious_disease_simulation";
          pyproject = true;
          version = "1.0.0";
          src = ./.;
          build-system = with python3Packages; [ poetry-core ];

          dependencies = with pkgs.python3Packages; [
            tkinter
            matplotlib
            numpy
            pygame
            setuptools
          ];

          # Note: the window icon at assets/virus_icon.png is loaded via a path relative
          # to the package source; in a nix-built install it won't resolve, but
          # set_display_icon silently degrades and the simulation runs fine without it.

          meta = {
            description = "A program to visualise simulations of an infectious disease spreading through a procedurally generated basic town.";
            homepage = "https://github.com/defunctdreams/infectious-disease-simulation";
            license = lib.licenses.gpl3;
            maintainers = with lib.maintainers; [ max-amb ];
            platforms = lib.platforms.linux;
          };
        };
  };
}
