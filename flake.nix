{
  description = "Python development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        shellFile = import ./shell.nix { inherit pkgs; };
        appFile = import ./run.nix { inherit pkgs; };
      in
      {
        #devShells.default = shellFile;
        devShells.run = appFile;
      }
    );
}
