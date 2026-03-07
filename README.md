# nixos-nanobot
Nanobot AI agent for NixOS with modules and configurations

## Goal
- Create ready to run out-of-the-box nixos configurations that have nanobot already installed, configured and can be used from non-technical users

## Current State
- nanobot package working
- Wizard server for easy configuration : under testing
- default nixos module : under testing

## NixOS Modules

This flake provides two NixOS modules: `nanobot` and `nanobot-wizard`.

### Quick Start

```nix
# flake.nix
{
  inputs.nixos-nanobot.url = "github:jjacke13/nixos-nanobot";

  outputs = { nixos-nanobot, ... }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      modules = [
        nixos-nanobot.nixosModules.nanobot
        nixos-nanobot.nixosModules.nanobot-wizard
        {
          services.nanobot.enable = true;
          services.nanobot-wizard.enable = true;
        }
      ];
    };
  };
}
```

### `services.nanobot` Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable` | bool | `false` | Enable the nanobot AI assistant service. |
| `package` | package | `self.packages.${system}.nanobot` | The nanobot package to use. |
| `dataDir` | path | `"/var/lib/nanobot"` | Directory for nanobot's mutable data and configuration. Config is stored at `<dataDir>/.nanobot/config.json`. |
| `user` | string | `"nanobot"` | User account under which nanobot runs. Created automatically as a system user. |
| `group` | string | `"nanobot"` | Group under which nanobot runs. Created automatically. |
| `extraPackages` | list of packages | `[]` | Extra packages added to the service PATH, available to the agent for tool use. Example: `[ pkgs.git pkgs.wget ]` |

#### What the module does

- Creates a system user and group for nanobot
- Runs `nanobot onboard` on first start to initialize workspace files
- Copies the default `config.json` into the data directory
- Adds a sudoers rule so the nanobot user can restart its own service (used by the wizard after saving config)
- Puts `nix`, `bash`, `jq`, `curl`, `coreutils`, and any `extraPackages` on the service PATH

### `services.nanobot-wizard` Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable` | bool | `false` | Enable the nanobot settings web UI. |
| `host` | string | `"0.0.0.0"` | Address the wizard web server binds to. |
| `port` | port | `8080` | Port the wizard web server listens on. |
| `configPath` | string | `"<nanobot.dataDir>/.nanobot/config.json"` | Path to the `config.json` file the wizard will edit. |

#### What the module does

- Runs a Python web server that provides a browser-based settings UI
- Runs as the same user/group as the nanobot service
- Edits nanobot's `config.json` and can restart the nanobot service after saving
- Stores PPQ credentials separately at `<nanobot.dataDir>/ppq-credit.json`

### Example: Full Configuration

```nix
{
  services.nanobot = {
    enable = true;
    dataDir = "/var/lib/nanobot";
    extraPackages = with pkgs; [ git wget python3 ];
  };

  services.nanobot-wizard = {
    enable = true;
    port = 9090;
    host = "127.0.0.1";  # local access only
  };
}
```

## Next steps
- More nanobot dependencies will be added, needed for skill installation etc.
- More capabilities to the wizard
- NixOS configurations will be added for small devices (Rpi4, Rpi5, Nanopi, Rpi02w). Nanobot is ultra-lightweight and can run easily on them
