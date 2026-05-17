# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path
from unittest.mock import MagicMock, patch


from legal_text_mcp_de.corpus.verifier import verify_bundle_signature


def test_verifier_calls_cosign_with_expected_args(tmp_path: Path):
    bundle = tmp_path / "corpus.tar.zst"
    bundle.write_bytes(b"test-bundle")
    sig = bundle.with_suffix(bundle.suffix + ".sig")
    sig.write_bytes(b"sig-data")
    cert = bundle.with_suffix(bundle.suffix + ".crt")
    cert.write_bytes(b"cert-data")

    cert_identity = (
        "https://github.com/klein-business/legal-text-mcp-de/.github/workflows/corpus-distribute.yml@refs/tags/v1.5.0"
    )
    issuer = "https://token.actions.githubusercontent.com"

    completed = MagicMock(returncode=0, stderr=b"", stdout=b"")
    with patch("subprocess.run", return_value=completed) as run:
        ok = verify_bundle_signature(bundle, cert_identity=cert_identity, oidc_issuer=issuer)
    assert ok
    call_args = run.call_args[0][0]
    assert call_args[0].endswith("cosign")
    assert "verify-blob" in call_args
    assert "--certificate-identity" in call_args
    assert cert_identity in call_args
    assert "--certificate-oidc-issuer" in call_args
    assert issuer in call_args
    assert str(sig) in call_args
    assert str(cert) in call_args
    assert str(bundle) in call_args


def test_verifier_returns_false_on_cosign_nonzero_exit(tmp_path: Path):
    bundle = tmp_path / "corpus.tar.zst"
    bundle.write_bytes(b"x")
    sig = bundle.with_suffix(bundle.suffix + ".sig")
    sig.write_bytes(b"x")
    cert = bundle.with_suffix(bundle.suffix + ".crt")
    cert.write_bytes(b"x")

    completed = MagicMock(returncode=1, stderr=b"verification failed", stdout=b"")
    with patch("subprocess.run", return_value=completed):
        ok = verify_bundle_signature(bundle, cert_identity="x")
    assert ok is False


def test_verifier_accepts_explicit_sidecar_paths(tmp_path: Path):
    bundle = tmp_path / "corpus.tar.zst"
    bundle.write_bytes(b"x")
    custom_sig = tmp_path / "alt.sig"
    custom_sig.write_bytes(b"x")
    custom_cert = tmp_path / "alt.crt"
    custom_cert.write_bytes(b"x")

    completed = MagicMock(returncode=0, stderr=b"", stdout=b"")
    with patch("subprocess.run", return_value=completed) as run:
        verify_bundle_signature(
            bundle,
            cert_identity="x",
            signature_path=custom_sig,
            certificate_path=custom_cert,
        )
    args = run.call_args[0][0]
    assert str(custom_sig) in args
    assert str(custom_cert) in args
