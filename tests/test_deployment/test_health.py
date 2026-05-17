# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from deployment.health import health_payload


def test_health_payload_has_required_fields():
    p = health_payload(corpus_version="2026-05", dataset_ready=True)
    assert p["status"] == "ok"
    assert p["corpus_version"] == "2026-05"
    assert isinstance(p["uptime_s"], int)
    assert p["uptime_s"] >= 0


def test_health_payload_degraded_when_dataset_missing():
    p = health_payload(corpus_version=None, dataset_ready=False)
    assert p["status"] == "degraded"
    assert p["corpus_version"] == "unknown"
