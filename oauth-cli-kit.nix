{
  lib,
  python3Packages,
  fetchPypi,
}:

python3Packages.buildPythonPackage rec {
  pname = "oauth-cli-kit";
  version = "0.1.3";
  pyproject = true;

  src = fetchPypi {
    pname = "oauth_cli_kit";
    inherit version;
    hash = "sha256-ZhKz3qGpfE3kp9O4KHZ9QvCnjq6Tvla5DFXTq2aOv7g=";
  };

  build-system = [
    python3Packages.hatchling
    python3Packages.hatch-vcs
  ];

  dependencies = with python3Packages; [
    httpx
    platformdirs
  ];

  doCheck = false;

  pythonImportsCheck = [ "oauth_cli_kit" ];

  meta = with lib; {
    description = "Reusable OAuth 2.0 + PKCE helpers for CLI applications";
    license = licenses.mit;
    maintainers = [ ];
  };
}
