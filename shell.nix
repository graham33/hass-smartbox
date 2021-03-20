with import <nixpkgs> {};
let
  python = python38.override {
    packageOverrides = pySelf: pySuper: {
      inherit (nur.repos.graham33.python3Packages) pytest-homeassistant-custom-component smartbox;
    };
  };
  pythonEnv = python.withPackages (ps: with ps; [
    flake8
    pytest
    pytest-aiohttp
    pytest-asyncio
    pytest-cov
    pytest-homeassistant-custom-component
    pytest-randomly
    pytest-sugar
    smartbox
    tox
  ]);
in mkShell {
  buildInputs = [
    black
    pythonEnv
  ];
}
