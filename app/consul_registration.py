"""
Consul Service Registration & KV Config for NotebookUM microservices.

- Registers/deregisters the service with HashiCorp Consul on startup/shutdown.
- Reads configuration and Traefik tags from Consul KV Store.
- Uses Consul HTTP API directly — no external dependencies required.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import socket
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────

# Support both CONSUL_URL (e.g. "http://consul:8500") and CONSUL_HOST+CONSUL_PORT
_consul_url_raw = os.getenv("CONSUL_URL", "")
if _consul_url_raw:
    _stripped = _consul_url_raw.replace("http://", "").replace("https://", "")
    if ":" in _stripped:
        CONSUL_HOST, _port_str = _stripped.rsplit(":", 1)
        CONSUL_PORT = int(_port_str)
    else:
        CONSUL_HOST = _stripped
        CONSUL_PORT = 8500
else:
    CONSUL_HOST = os.getenv("CONSUL_HOST", "consul")
    CONSUL_PORT = int(os.getenv("CONSUL_PORT", "8500"))

CONSUL_TOKEN = os.getenv("CONSUL_TOKEN", "2be22662-4819-4a0c-81d9-b3f50c4c389c")
CONSUL_BASE_URL = f"http://{CONSUL_HOST}:{CONSUL_PORT}"


def _get_container_ip() -> str:
    """Get the container's IP address for Consul registration."""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return "127.0.0.1"


def _consul_request(method: str, path: str, body: dict | None = None) -> bool:
    """Make a request to the Consul HTTP API."""
    url = f"{CONSUL_BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {
        "Content-Type": "application/json",
        "X-Consul-Token": CONSUL_TOKEN,
    }

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        logger.warning("Consul request failed: %s %s -> %s", method, path, exc)
        return False


# ─── Consul KV Store ─────────────────────────────────────────────────────────

def fetch_kv_config(service_name: str) -> dict[str, str]:
    """
    Read all configuration keys for a service from Consul KV.

    Reads from: config/{service_name}/?recurse
    Returns a flat dict, e.g. {"PORT": "5000", "HOST": "0.0.0.0"}
    Traefik sub-keys are excluded (handled by fetch_traefik_tags).
    """
    url = f"{CONSUL_BASE_URL}/v1/kv/config/{service_name}/?recurse"
    headers = {"X-Consul-Token": CONSUL_TOKEN}
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            entries = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        logger.warning("Failed to read Consul KV for %s: %s", service_name, exc)
        return {}

    config: dict[str, str] = {}
    prefix = f"config/{service_name}/"

    for entry in entries:
        key: str = entry.get("Key", "")
        raw_value = entry.get("Value")

        # Skip folder entries (no value) and traefik sub-keys
        if raw_value is None:
            continue

        relative_key = key.removeprefix(prefix)
        if relative_key.startswith("traefik/"):
            continue  # handled by fetch_traefik_tags

        # Consul KV values are base64 encoded
        value = base64.b64decode(raw_value).decode("utf-8")
        config[relative_key] = value

    logger.info("✓ Loaded %d config keys from Consul KV for %s", len(config), service_name)
    return config


def fetch_traefik_tags(service_name: str) -> list[str]:
    """
    Build Traefik-compatible tags from Consul KV sub-keys.

    Reads from: config/{service_name}/traefik/*
    Returns a list like:
      ["traefik.enable=true",
       "traefik.http.routers.{name}.rule=Host(`...`)",
       "traefik.http.routers.{name}.entryPoints=http,https",
       "traefik.http.services.{name}.loadbalancer.server.port=5000"]
    """
    url = f"{CONSUL_BASE_URL}/v1/kv/config/{service_name}/traefik/?recurse"
    headers = {"X-Consul-Token": CONSUL_TOKEN}
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            entries = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        logger.warning("Failed to read Traefik tags from Consul KV for %s: %s", service_name, exc)
        return []

    traefik_kv: dict[str, str] = {}
    prefix = f"config/{service_name}/traefik/"

    for entry in entries:
        key: str = entry.get("Key", "")
        raw_value = entry.get("Value")
        if raw_value is None:
            continue
        relative_key = key.removeprefix(prefix)
        traefik_kv[relative_key] = base64.b64decode(raw_value).decode("utf-8")

    if not traefik_kv:
        return []

    # Build standard Traefik tags
    tags: list[str] = []
    if "enable" in traefik_kv:
        tags.append(f"traefik.enable={traefik_kv['enable']}")
    if "router_rule" in traefik_kv:
        tags.append(f"traefik.http.routers.{service_name}.rule={traefik_kv['router_rule']}")
    if "entrypoints" in traefik_kv:
        tags.append(f"traefik.http.routers.{service_name}.entryPoints={traefik_kv['entrypoints']}")
    if "lb_port" in traefik_kv:
        tags.append(f"traefik.http.services.{service_name}.loadbalancer.server.port={traefik_kv['lb_port']}")

    logger.info("✓ Loaded %d Traefik tags from Consul KV for %s", len(tags), service_name)
    return tags


# ─── Service Registration ────────────────────────────────────────────────────

def register_service(
    service_name: str,
    service_port: int,
    health_check_path: str = "/health",
    tags: list[str] | None = None,
) -> bool:
    """
    Register this service instance with Consul.

    If tags are not provided, they are fetched automatically from Consul KV.
    """
    # If no tags passed, read from Consul KV
    if tags is None:
        tags = fetch_traefik_tags(service_name)

    container_ip = _get_container_ip()
    service_id = f"{service_name}-{container_ip}-{service_port}"

    payload = {
        "ID": service_id,
        "Name": service_name,
        "Address": container_ip,
        "Port": service_port,
        "Tags": tags,
        "Check": {
            "HTTP": f"http://{container_ip}:{service_port}{health_check_path}",
            "Interval": "15s",
            "Timeout": "5s",
            "DeregisterCriticalServiceAfter": "90s",
        },
    }

    success = _consul_request("PUT", "/v1/agent/service/register", payload)
    if success:
        logger.info(
            "✓ Registered in Consul: %s (id=%s, addr=%s:%d, tags=%d)",
            service_name, service_id, container_ip, service_port, len(tags),
        )
    else:
        logger.error(
            "✗ Failed to register in Consul: %s (addr=%s:%d)",
            service_name, container_ip, service_port,
        )
    return success


def deregister_service(service_name: str, service_port: int) -> bool:
    """Deregister this service instance from Consul."""
    container_ip = _get_container_ip()
    service_id = f"{service_name}-{container_ip}-{service_port}"

    success = _consul_request("PUT", f"/v1/agent/service/deregister/{service_id}")
    if success:
        logger.info("✓ Deregistered from Consul: %s (id=%s)", service_name, service_id)
    else:
        logger.warning("✗ Failed to deregister from Consul: %s", service_name)
    return success
