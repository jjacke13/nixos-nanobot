{ self }:

{ config, lib, pkgs, ... }:

let
  cfg = config.services.nanobot;
  defaultConfig = ./config.json;
in
{
  options.services.nanobot = {
    enable = lib.mkEnableOption "nanobot personal AI assistant";

    package = lib.mkOption {
      type = lib.types.package;
      default = self.packages.${pkgs.system}.nanobot;
      description = "The nanobot package to use.";
    };

    dataDir = lib.mkOption {
      type = lib.types.path;
      default = "/var/lib/nanobot";
      description = "Directory for nanobot's mutable data and configuration.";
    };

    user = lib.mkOption {
      type = lib.types.str;
      default = "nanobot";
      description = "User account under which nanobot runs.";
    };

    group = lib.mkOption {
      type = lib.types.str;
      default = "nanobot";
      description = "Group under which nanobot runs.";
    };

    extraPackages = lib.mkOption {
      type = lib.types.listOf lib.types.package;
      default = [ ];
      example = lib.literalExpression "[ pkgs.git pkgs.wget ]";
      description = "Extra packages to add to the service PATH, available to the agent for tool use.";
    };
  };

  config = lib.mkIf cfg.enable {
    users.users.${cfg.user} = {
      isSystemUser = true;
      group = cfg.group;
      home = cfg.dataDir;
      createHome = true;
    };

    users.groups.${cfg.group} = { };

    # Allow the nanobot user to restart its own service without a password
    # (needed by the settings web form after saving config)
    security.sudo.extraRules = [
      {
        users = [ cfg.user ];
        commands = [
          { command = "/run/current-system/sw/bin/systemctl restart nanobot.service"; options = [ "NOPASSWD" ]; }
        ];
      }
    ];

    systemd.services.nanobot = {
      description = "Nanobot AI Assistant";
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];

      preStart = ''
        # First run: let onboard create workspace files, then replace config with ours
        if [ ! -f ${cfg.dataDir}/.nanobot/.onboarded ]; then
          ${cfg.package}/bin/nanobot onboard
          cp ${defaultConfig} ${cfg.dataDir}/.nanobot/config.json
          chmod 600 ${cfg.dataDir}/.nanobot/config.json
          touch ${cfg.dataDir}/.nanobot/.onboarded
        fi
      '';

      path = [
        pkgs.nix
        pkgs.bash
        pkgs.jq
        pkgs.curl
        pkgs.coreutils
        self.packages.${pkgs.system}.nanobot
      ] ++ cfg.extraPackages;

      serviceConfig = {
        Type = "simple";
        User = cfg.user;
        Group = cfg.group;
        ExecStart = "${cfg.package}/bin/nanobot gateway";
        WorkingDirectory = cfg.dataDir;
        Restart = "on-failure";
        RestartSec = 10;

        # Set HOME so nanobot finds ~/.nanobot/config.json
        Environment = "HOME=${cfg.dataDir}";

        PrivateTmp = true;
      };
    };
  };
}
