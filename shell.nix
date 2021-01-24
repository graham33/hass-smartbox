{ pkgs ? import <nixpkgs> {} }:
let
  python = pkgs.python3.withPackages (ps: with ps; [ flake8
                                                     yapf
                                                   ]);
in
pkgs.mkShell {
  nativeBuildInputs = [ python ];
}
