"""
Privacy monitor — logs every network-capable operation so the local-only
guarantee is auditable.
"""
from __future__ import annotations

import datetime as _dt
import os
import socket
from pathlib import Path

from .config import get, ensure_dirs
from .logger import get_logger

_log = get_logger(__name__)


def _audit_path() -> Path:
    p = Path(get("privacy", "audit_file", "data/privacy_audit.log"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def audit(event: str, details: str = "") -> None:
    """Append a timestamped audit entry."""
    line = f"{_dt.datetime.utcnow().isoformat()}Z | {event} | {details}\n"
    with _audit_path().open("a", encoding="utf-8") as f:
        f.write(line)
    _log.info("PRIVACY %s %s", event, details)


def check_endpoint_is_local(url: str) -> bool:
    """Return True if the URL host resolves to localhost/loopback only."""
    from urllib.parse import urlparse
    host = urlparse(url).hostname or ""
    if host in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        # If it resolves to something else, it is not local
        infos = socket.getaddrinfo(host, None)
        return all(i[4][0] in ("127.0.0.1", "::1") for i in infos)
    except socket.gaierror:
        return False


def assert_local(url: str) -> None:
    """Raise if a URL is non-local — used before every outbound call."""
    if not check_endpoint_is_local(url):
        audit("BLOCKED_NON_LOCAL", url)
        raise RuntimeError(f"Blocked non-local network call: {url}")
    audit("ALLOWED_LOCAL_CALL", url)


def log_privacy_banner() -> None:
    """Write a startup banner to the audit log."""
    audit(
        "STARTUP",
        f"pid={os.getpid()} — all processing local, no outbound traffic permitted",
    )