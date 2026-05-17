# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Verifies corpus bundle signatures using cosign keyless.

Sidecar layout (default):
    corpus.tar.zst       — the bundle itself
    corpus.tar.zst.sig   — cosign signature (base64)
    corpus.tar.zst.crt   — Fulcio short-lived certificate

The verifier shells out to the ``cosign`` binary. It is the operator's
responsibility to install cosign (we document this in
``docs/operations/verify-with-cosign.md``).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def verify_bundle_signature(
    bundle_path: Path,
    *,
    cert_identity: str,
    signature_path: Path | None = None,
    certificate_path: Path | None = None,
    oidc_issuer: str = "https://token.actions.githubusercontent.com",
    cosign_bin: str = "cosign",
) -> bool:
    """Run ``cosign verify-blob`` against the bundle.

    Returns ``True`` when cosign exits with status 0, ``False`` otherwise.
    Does not raise on verification failure — callers decide how to react.
    """
    sig = signature_path or bundle_path.with_suffix(bundle_path.suffix + ".sig")
    cert = certificate_path or bundle_path.with_suffix(bundle_path.suffix + ".crt")
    cmd = [
        cosign_bin,
        "verify-blob",
        "--certificate-identity",
        cert_identity,
        "--certificate-oidc-issuer",
        oidc_issuer,
        "--signature",
        str(sig),
        "--certificate",
        str(cert),
        str(bundle_path),
    ]
    result = subprocess.run(cmd, capture_output=True, check=False)
    return result.returncode == 0
