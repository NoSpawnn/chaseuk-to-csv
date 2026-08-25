{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/packages/
  packages = [];

  # https://devenv.sh/languages/
  languages.python = {
      enable = true;
      venv.enable = true;
  };
}
