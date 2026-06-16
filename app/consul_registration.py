"""
Consul Service Registration for NotebookUM microservices.

Registers/deregisters the service with HashiCorp Consul on startup/shutdown.
Uses Consul HTTP API directly — no external dependencies required.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────

CONSUL_HOST = os.getenv("CONSUL_HOST", "consul")
CONSUL_PORT = int(os.getenv("CONSUL_PORT", "8500"))
CONSUL_TOKEN = os.getenv("CONSUL_TOKEN", "ac80cdb0-2ca6-4182-ae14-15158c33c095")
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


def register_service(
    service_name: str,
    service_port: int,
    health_check_path: str = "/health",
    tags: list[str] | None = None,
) -> bool:
    """
    Register this service instance with Consul.

    Args:
        service_name: Name to register in Consul (e.g. 'user-service')
        service_port: Port the service listens on
        health_check_path: HTTP health check endpoint
        tags: Traefik-compatible tags for routing

    Returns:
        True if registration succeeded
    """
    container_ip = _get_container_ip()
    service_id = f"{service_name}-{container_ip}-{service_port}"

    payload = {
        "ID": service_id,
        "Name": service_name,
        "Address": container_ip,
        "Port": service_port,
        "Tags": tags or [],
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
            "✓ Registered in Consul: %s (id=%s, addr=%s:%d)",
            service_name, service_id, container_ip, service_port,
        )
    else:
        logger.error(
            "✗ Failed to register in Consul: %s (addr=%s:%d)",
            service_name, container_ip, service_port,
        )
    return success


def deregister_service(service_name: str, service_port: int) -> bool:
    """
    Deregister this service instance from Consul.

    Returns:
        True if deregistration succeeded
    """
    container_ip = _get_container_ip()
    service_id = f"{service_name}-{container_ip}-{service_port}"

    success = _consul_request("PUT", f"/v1/agent/service/deregister/{service_id}")
    if success:
        logger.info("✓ Deregistered from Consul: %s (id=%s)", service_name, service_id)
    else:
        logger.warning("✗ Failed to deregister from Consul: %s", service_name)
    return success
