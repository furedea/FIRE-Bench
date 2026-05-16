{
  description = "FIRE-Bench development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-25.11-darwin";
  };

  outputs =
    { nixpkgs, ... }:
    let
      system = "aarch64-darwin";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfreePredicate =
          pkg:
          builtins.elem (nixpkgs.lib.getName pkg) [
            "claude-code"
          ];
      };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          claude-code
          commitlint
          deadnix
          lefthook
          ls-lint
          nixfmt-rfc-style
          nodejs_22
          statix
          uv
        ];

        env = {
          UV_MANAGED_PYTHON = "1";
        };

        shellHook = ''
          if [ -d .venv/bin ]; then
            export PATH="$PWD/.venv/bin:$PATH"
          fi
        '';
      };
    };
}
