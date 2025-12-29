{pkgs ? (import (import ./npins).nixpkgs {})}:
pkgs.mkShellNoCC {
  packages = with pkgs; [
    alejandra
    nil
    pyrefly
    ruff
  ];
}
