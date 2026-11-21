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

