{
  description = "Nix flake for nanobot - ultra-lightweight personal AI assistant";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs, ... }:
    {
    packages = {
      x86_64-linux = let
        pkgs = nixpkgs.legacyPackages.x86_64-linux;
        oauth-cli-kit = pkgs.callPackage ./oauth-cli-kit.nix { };
      in {
        inherit oauth-cli-kit;
        nanobot = pkgs.callPackage ./package.nix { inherit oauth-cli-kit; };
        default = self.packages.x86_64-linux.nanobot;
      };

      aarch64-linux = let
        pkgs = nixpkgs.legacyPackages.aarch64-linux;
        oauth-cli-kit = pkgs.callPackage ./oauth-cli-kit.nix { };
      in {
        inherit oauth-cli-kit;
        nanobot = pkgs.callPackage ./package.nix { inherit oauth-cli-kit; };
        default = self.packages.aarch64-linux.nanobot;
      };
    };

    nixosModules = {
      nanobot = import ./module.nix { inherit self; };
      nanobot-wizard = import ./wizard-module.nix { inherit self; };
      default = self.nixosModules.nanobot;
    };
    
    nixosConfigurations= {
     ## To be added     
    };
  };
}
