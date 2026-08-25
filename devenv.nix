{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/packages/
  packages = [ pkgs.hledger ];

  # https://devenv.sh/languages/
  languages.python = {
      enable = true;
      venv.enable = true;
  };
}
