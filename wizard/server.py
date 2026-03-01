#!/usr/bin/env python3
"""
Nanobot Setup Wizard - Web-based configuration for non-technical users.

Serves a multi-step form to configure AI provider, model, and Telegram.
Writes to config.json and restarts the nanobot service.

Usage:
    python server.py [--port 8080] [--config /path/to/config.json]

Environment variables (override CLI args):
    WIZARD_PORT         - Port to listen on (default: 8080)
    WIZARD_CONFIG_PATH  - Path to config.json
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

WIZARD_DIR = Path(__file__).parent
CONFIG_PATH = os.environ.get(
    "WIZARD_CONFIG_PATH",
    str(WIZARD_DIR / "config.json"),
)
HOST = os.environ.get("WIZARD_HOST", "0.0.0.0")
PORT = int(os.environ.get("WIZARD_PORT", "8080"))
INDEX_PATH = WIZARD_DIR / "index.html"
PPQ_CREDIT_PATH = os.environ.get(
    "WIZARD_PPQ_CREDIT_PATH",
    "/var/lib/nanobot/ppq-credit.json",
)
PPQ_API_URL = "https://api.ppq.ai"

# Keys whose values should be redacted in GET /api/config
REDACT_KEYS = {"apiKey", "api_key", "token"}


def read_config():
    """Read current config.json, return dict."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_config(data):
    """Write config to config.json atomically."""
    config_dir = os.path.dirname(CONFIG_PATH)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=config_dir or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.rename(tmp_path, CONFIG_PATH)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def deep_merge(base, overlay):
    """Recursively merge overlay into base. Overlay values take precedence."""
    if base is None:
        return overlay
    if overlay is None:
        return base
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = dict(base)
        for k, v in overlay.items():
            result[k] = deep_merge(result.get(k), v)
        return result
    return overlay


def redact_secrets(obj):
    """Recursively redact sensitive fields in config for GET responses."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if key in REDACT_KEYS and isinstance(value, str) and len(value) > 6:
                # Show first 3 chars, mask middle, show last 3 chars
                result[key] = value[:3] + "****" + value[-3:]
            elif key in REDACT_KEYS and isinstance(value, str) and value:
                result[key] = "****"
            elif isinstance(value, (dict, list)):
                result[key] = redact_secrets(value)
            else:
                result[key] = value
        return result
    elif isinstance(obj, list):
        return [redact_secrets(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
BOT_TOKEN_RE = re.compile(r"^\d{8,10}:[A-Za-z0-9_-]{30,50}$")
USER_ID_RE = re.compile(r"^\d{5,13}$")
URL_RE = re.compile(r"^https?://\S+$")


def validate_config(data):
    """Validate incoming config data. Returns (ok, errors) tuple."""
    errors = []

    if not isinstance(data, dict):
        return False, ["Config must be a JSON object."]

    # --- Providers ---
    providers = data.get("providers")
    if providers is not None:
        if not isinstance(providers, dict):
            errors.append("'providers' must be an object.")
        else:
            for prov_name, prov in providers.items():
                if not isinstance(prov, dict):
                    errors.append(f"'providers.{prov_name}' must be an object.")
                    continue
                api_base = prov.get("apiBase")
                if api_base is not None and api_base != "" and not URL_RE.match(api_base):
                    errors.append(f"providers.{prov_name}: invalid apiBase URL.")
                api_key = prov.get("apiKey")
                if api_key is not None and not isinstance(api_key, str):
                    errors.append(f"providers.{prov_name}: apiKey must be a string.")

    # --- Agents ---
    agents = data.get("agents")
    if agents is not None:
        if not isinstance(agents, dict):
            errors.append("'agents' must be an object.")
        else:
            defaults = agents.get("defaults")
            if defaults is not None and not isinstance(defaults, dict):
                errors.append("'agents.defaults' must be an object.")

    # --- Channels (Telegram) ---
    channels = data.get("channels")
    if channels is not None:
        if not isinstance(channels, dict):
            errors.append("'channels' must be an object.")
        else:
            tg = channels.get("telegram")
            if tg is not None:
                if not isinstance(tg, dict):
                    errors.append("'channels.telegram' must be an object.")
                else:
                    if tg.get("enabled") is True:
                        token = tg.get("token", "")
                        if not token:
                            errors.append("Telegram bot token is required when enabled.")
                        elif not BOT_TOKEN_RE.match(token):
                            errors.append("Invalid Telegram bot token format.")
                    allow_from = tg.get("allowFrom")
                    if allow_from is not None:
                        if not isinstance(allow_from, list):
                            errors.append("'allowFrom' must be a list.")
                        else:
                            for uid in allow_from:
                                if uid and not USER_ID_RE.match(str(uid)):
                                    errors.append(f"Invalid Telegram user ID: '{uid}'. Must be 5-13 digits.")

    return len(errors) == 0, errors


def restart_nanobot():
    """Restart the nanobot service."""
    try:
        subprocess.run(
            ["/run/wrappers/bin/sudo", "/run/current-system/sw/bin/systemctl", "restart", "nanobot.service"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True, "Service restarted successfully."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to restart: {e.stderr.decode()}"
    except FileNotFoundError:
        return False, "sudo or systemctl not found. Are you running on NixOS?"


class WizardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the setup wizard."""

    def do_GET(self):
        if self.path == "/":
            self._serve_index()
        elif self.path == "/api/config":
            self._handle_get_config()
        elif self.path == "/api/ppq/balance":
            self._handle_ppq_balance()
        elif self.path == "/api/ppq/credit":
            self._handle_ppq_credit()
        elif self.path.startswith("/api/models"):
            self._handle_models()
        elif self.path == "/style.css":
            self._serve_file("style.css", "text/css; charset=utf-8")
        elif self.path.startswith("/schemas/") and self.path.endswith(".js"):
            self._serve_static("schemas")
        elif self.path.startswith("/i18n/") and self.path.endswith(".js"):
            self._serve_static("i18n")
        elif self.path == "/ppq.png":
            self._serve_file("ppq.png", "image/png")
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/api/config":
            self._handle_save()
        elif self.path == "/api/ppq/register":
            self._handle_ppq_register()
        else:
            self._send_json(404, {"error": "Not found"})

    def _serve_index(self):
        try:
            content = INDEX_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self._send_json(500, {"error": "index.html not found"})

    def _serve_file(self, filename, content_type):
        filepath = WIZARD_DIR / filename
        if not filepath.is_file():
            self._send_json(404, {"error": "Not found"})
            return
        content = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_static(self, subdir):
        # Only allow simple filenames -- no path traversal
        filename = self.path.split("/")[-1]
        if not filename.endswith(".js") or "/" in filename or "\\" in filename:
            self._send_json(404, {"error": "Not found"})
            return
        filepath = WIZARD_DIR / subdir / filename
        if not filepath.is_file():
            self._send_json(404, {"error": "Not found"})
            return
        try:
            content = filepath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self._send_json(404, {"error": "Not found"})

    MAX_BODY = 65536  # 64 KB

    def _handle_get_config(self):
        """Return config with secrets redacted."""
        config = read_config()
        redacted = redact_secrets(config)
        self._send_json(200, redacted)

    def _handle_save(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > self.MAX_BODY:
                self._send_json(413, {"error": "Request too large"})
                return
            body = self.rfile.read(length)
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {"error": "Invalid JSON"})
            return

        # For PPQ provider: inject the API key from ppq-credit.json
        # (the apiKey field is hidden in the UI for PPQ)
        custom_provider = data.get("providers", {}).get("custom", {})
        if custom_provider.get("apiBase") == "https://api.ppq.ai" or (
            custom_provider and not custom_provider.get("apiKey")
        ):
            try:
                with open(PPQ_CREDIT_PATH, "r") as f:
                    credit = json.load(f)
                ppq_key = credit.get("api_key", "")
                if ppq_key and "custom" in data.get("providers", {}):
                    data["providers"]["custom"]["apiKey"] = ppq_key
            except (FileNotFoundError, json.JSONDecodeError):
                pass

        # Merge with existing config to preserve fields not in the form
        existing = read_config()
        merged = deep_merge(existing, data)

        # Validate the merged result (not raw POST, which may omit unchanged secrets)
        valid, errors = validate_config(merged)
        if not valid:
            self._send_json(400, {"success": False, "errors": errors})
            return

        write_config(merged)

        ok, msg = restart_nanobot()
        status = 200 if ok else 500
        self._send_json(status, {"success": ok, "message": msg})

    def _handle_models(self):
        """Proxy model listing from provider API."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        base_url = params.get("baseUrl", [""])[0]
        api_key = params.get("apiKey", [""])[0]

        if not base_url or not URL_RE.match(base_url):
            self._send_json(400, {"error": "Invalid base URL"})
            return

        url = base_url.rstrip("/")
        if url.endswith("/v1"):
            url += "/models"
        else:
            url += "/v1/models"

        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            models = []
            for m in data.get("data", []):
                if isinstance(m, dict) and m.get("id"):
                    models.append({"id": m["id"]})
            models.sort(key=lambda x: x["id"])
            self._send_json(200, {"models": models})
        except Exception as e:
            self._send_json(502, {"error": str(e)})

    def _handle_ppq_register(self):
        """Create a new PPQ account and return the API key."""
        # Check if we already have a credit stored
        try:
            with open(PPQ_CREDIT_PATH, "r") as f:
                existing = json.load(f)
            if existing.get("api_key"):
                self._send_json(200, {
                    "api_key": existing["api_key"],
                    "credit_id": existing.get("credit_id", ""),
                    "existing": True,
                })
                return
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Call PPQ account creation API
        req = urllib.request.Request(
            f"{PPQ_API_URL}/accounts/create",
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            self._send_json(502, {"error": f"PPQ registration failed: {e}"})
            return

        api_key = data.get("api_key", "")
        credit_id = data.get("credit_id", "")
        if not api_key:
            self._send_json(502, {"error": "PPQ returned no API key."})
            return

        # Save credit info to file
        credit_dir = os.path.dirname(PPQ_CREDIT_PATH)
        if credit_dir:
            os.makedirs(credit_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=credit_dir or ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump({"credit_id": credit_id, "api_key": api_key}, f, indent=2)
            os.rename(tmp_path, PPQ_CREDIT_PATH)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
            raise

        self._send_json(200, {
            "api_key": api_key,
            "credit_id": credit_id,
            "existing": False,
        })

    def _handle_ppq_balance(self):
        """Return the PPQ credit balance using credit_id from ppq-credit.json."""
        try:
            with open(PPQ_CREDIT_PATH, "r") as f:
                credit_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._send_json(404, {"error": "No PPQ credit file found."})
            return

        credit_id = credit_data.get("credit_id", "")
        if not credit_id:
            self._send_json(404, {"error": "No credit_id in PPQ credit file."})
            return

        payload = json.dumps({"credit_id": credit_id}).encode()
        req = urllib.request.Request(
            f"{PPQ_API_URL}/credits/balance",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            self._send_json(200, data)
        except Exception as e:
            self._send_json(502, {"error": f"Failed to fetch balance: {e}"})

    def _handle_ppq_credit(self):
        """Save or return the PPQ credit_id."""
        try:
            with open(PPQ_CREDIT_PATH, "r") as f:
                credit_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            credit_data = {}
        self._send_json(200, {
            "credit_id": credit_data.get("credit_id", ""),
        })

    def _send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[wizard] {format % args}")


def main():
    global CONFIG_PATH

    port = PORT

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--config" and i + 1 < len(args):
            CONFIG_PATH = args[i + 1]
            i += 2
        else:
            i += 1

    server = HTTPServer((HOST, port), WizardHandler)
    print(f"[wizard] Nanobot Setup Wizard running on http://{HOST}:{port}")
    print(f"[wizard] Config path: {CONFIG_PATH}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[wizard] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
