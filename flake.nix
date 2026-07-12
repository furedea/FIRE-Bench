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
      seJavaPackages =
        with pkgs;
        [
          ant
          diffutils
          git
          gnupatch
          jdk11
          maven
          perl
          perlPackages.Appcpanminus
          subversion
          wget
        ]
        ++ nixpkgs.lib.optional (pkgs ? defects4j) pkgs.defects4j;
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages =
          (with pkgs; [
            claude-code
            commitlint
            deadnix
            lefthook
            ls-lint
            nixfmt-rfc-style
            nodejs_22
            statix
            uv
          ])
          ++ seJavaPackages;

        env = {
          UV_MANAGED_PYTHON = "1";
        };

        shellHook = ''
          export PATH="${pkgs.perl}/bin:$PATH"
          if [ -d .venv/bin ]; then
            export PATH="$PWD/.venv/bin:$PATH"
          fi
          if [ -d external-artifacts/defects4j/framework/bin ]; then
            export DEFECTS4J_HOME="$PWD/external-artifacts/defects4j"
            export FIRE_BENCH_PERL_BIN="${pkgs.perl}/bin/perl"
            export PATH="$DEFECTS4J_HOME/framework/bin:$PATH"
            if [ -d "$DEFECTS4J_HOME/local/lib/perl5" ]; then
              export PERL5LIB="$DEFECTS4J_HOME/local/lib/perl5:$PERL5LIB"
              export PATH="$DEFECTS4J_HOME/local/bin:$PATH"
            fi
          fi
        '';
      };
    };
}
