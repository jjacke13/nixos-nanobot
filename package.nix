{
  lib,
  python3Packages,
  fetchFromGitHub,
  oauth-cli-kit,
}:

python3Packages.buildPythonPackage rec {
  pname = "nanobot-ai";
  version = "0.1.4.post2";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "HKUDS";
    repo = "nanobot";
    rev = "v${version}";
    hash = "sha256-5UC3U5Z2BfONImsrJMI5gNLXFLLYONcjy4+Bp1EX93A=";
  };

  build-system = [
    python3Packages.hatchling
  ];

  # Remove dependencies not in nixpkgs
  postPatch = ''
    substituteInPlace pyproject.toml \
      --replace-fail '"dingtalk-stream>=0.24.0,<1.0.0",' "" \
      --replace-fail '"lark-oapi>=1.5.0,<2.0.0",' "" \
      --replace-fail '"qq-botpy>=1.2.0,<2.0.0",' "" \
      --replace-fail '"slackify-markdown>=0.2.0,<1.0.0",' ""
  '';

  pythonRelaxDeps = true;

  dependencies = with python3Packages; [
    # Core
    typer
    litellm
    pydantic
    pydantic-settings

    # Networking
    websockets
    websocket-client
    httpx
    socksio
    python-socks

    # Utilities
    loguru
    readability-lxml
    rich
    croniter
    prompt-toolkit
    msgpack
    json-repair

    # Chat platforms (available in nixpkgs)
    python-telegram-bot
    python-socketio
    slack-sdk

    # MCP support
    mcp

    # Packaged locally
    oauth-cli-kit

    # Note: Patched out (not in nixpkgs):
    # - dingtalk-stream, lark-oapi, qq-botpy (Chinese platforms)
    # - slackify-markdown (Slack formatting)
  ];

  # Skip tests for now - they require network access
  doCheck = false;

  pythonImportsCheck = [ "nanobot" ];

  meta = with lib; {
    description = "Ultra-lightweight personal AI assistant (~4000 LOC)";
    homepage = "https://github.com/HKUDS/nanobot";
    license = licenses.mit;
    maintainers = [ ];
    mainProgram = "nanobot";
  };
}
