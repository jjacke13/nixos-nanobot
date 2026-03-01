{ self }:

{ config, lib, pkgs, ... }:

let
  cfg = config.services.nanobot-wizard;
  nanobotCfg = config.services.nanobot;
  wizardSrc = ./wizard;
in
{
  options.services.nanobot-wizard = {
    enable = lib.mkEnableOption "nanobot settings web UI";

    host = lib.mkOption {
      type = lib.types.str;
      default = "0.0.0.0";
      description = "Address the wizard web server binds to.";
    };

    port = lib.mkOption {
      type = lib.types.port;
      default = 8080;
      description = "Port the wizard web server listens on.";
    };

    configPath = lib.mkOption {
      type = lib.types.str;
      default = "${nanobotCfg.dataDir}/.nanobot/config.json";
      description = "Path to the nanobot config.json the wizard will edit.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.nanobot-wizard = {
      description = "Nanobot Settings Web UI";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        Type = "simple";
        User = nanobotCfg.user;
        Group = nanobotCfg.group;
        ExecStart = "${pkgs.python3}/bin/python3 ${wizardSrc}/server.py";
        WorkingDirectory = toString wizardSrc;
        Restart = "on-failure";
        RestartSec = 5;

        Environment = [
          "HOME=${nanobotCfg.dataDir}"
          "WIZARD_HOST=${cfg.host}"
          "WIZARD_PORT=${toString cfg.port}"
          "WIZARD_CONFIG_PATH=${cfg.configPath}"
          "WIZARD_PPQ_CREDIT_PATH=${nanobotCfg.dataDir}/ppq-credit.json"
        ];

      };
    };
  };
}
