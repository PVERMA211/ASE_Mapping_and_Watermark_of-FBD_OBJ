"""
watermark.py
============
Steps 3, 4 & 5 – Generate, embed, and verify a cryptographic watermark
for a mapped FBDObject.

Watermark schema stored in fbd.metadata["watermark"]:
{
    "owner":      "<owner string>",
    "timestamp":  "<ISO-8601 UTC>",
    "hash":       "<SHA-256 hex digest of canonical block fingerprint>",
    "signature":  "<HMAC-SHA256 of hash+owner+timestamp using a secret key>"
}
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any

from fbd_mapper import FBDObject


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_SECRET_ENV = "FBD_WATERMARK_SECRET"
_WATERMARK_KEY = "watermark"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_watermark(fbd: FBDObject, owner: str, secret: str | None = None) -> dict[str, str]:
    """
    Compute and return a watermark dict for the given FBDObject.

    Parameters
    ----------
    fbd:    The mapped FBD object.
    owner:  Ownership string (name, org, etc.).
    secret: Optional HMAC secret; falls back to env var FBD_WATERMARK_SECRET
            or a deterministic default (not secure for production).
    """
    secret = _resolve_secret(secret)
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    content_hash = _hash_fbd_content(fbd)
    signature = _sign(content_hash, owner, timestamp, secret)

    return {
        "owner": owner,
        "timestamp": timestamp,
        "hash": content_hash,
        "signature": signature,
    }


def embed_watermark(fbd: FBDObject, watermark: dict[str, str]) -> FBDObject:
    """
    Embed the watermark dict into fbd.metadata["watermark"] in place.
    Returns the same FBDObject for chaining convenience.
    """
    fbd.metadata[_WATERMARK_KEY] = watermark
    return fbd


def verify_watermark(fbd: FBDObject, secret: str | None = None) -> bool:
    """
    Verify the embedded watermark against the current FBD content.

    Returns True if the watermark is intact and the signature matches.
    Raises KeyError if no watermark is embedded.
    """
    wm: dict[str, str] = fbd.metadata.get(_WATERMARK_KEY, {})
    if not wm:
        raise KeyError("No watermark found in FBD metadata.")

    secret = _resolve_secret(secret)

    # 1. Re-compute content hash and compare
    expected_hash = _hash_fbd_content(fbd)
    if not hmac.compare_digest(expected_hash, wm.get("hash", "")):
        return False

    # 2. Re-compute signature and compare
    expected_sig = _sign(wm["hash"], wm["owner"], wm["timestamp"], secret)
    return hmac.compare_digest(expected_sig, wm.get("signature", ""))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_secret(secret: str | None) -> str:
    if secret:
        return secret
    env_secret = os.environ.get(_DEFAULT_SECRET_ENV, "")
    if env_secret:
        return env_secret
    # Non-production fallback – always warn in real deployments
    return "default-insecure-secret"


def _hash_fbd_content(fbd: FBDObject) -> str:
    """SHA-256 of a canonical JSON representation of the FBD blocks."""
    # Exclude metadata to avoid hash-of-hash circular dependency
    canonical: dict[str, Any] = {
        "name": fbd.name,
        "blocks": sorted(
            [b.to_dict() for b in fbd.blocks], key=lambda b: b["block_id"]
        ),
        "connections": sorted(
            [c.to_dict() for c in fbd.connections],
            key=lambda c: (c["from"], c["to"]),
        ),
    }
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sign(content_hash: str, owner: str, timestamp: str, secret: str) -> str:
    """HMAC-SHA256 over the concatenated watermark fields."""
    message = f"{content_hash}|{owner}|{timestamp}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
