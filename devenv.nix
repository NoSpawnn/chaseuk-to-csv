{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/packages/
  packages = [ pkgs.hledger pkgs.ruff ];

  # https://devenv.sh/languages/
  languages.python = {
      enable = true;
      venv.enable = true;
  };
}
