# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import pytest


@pytest.fixture
def sample_law_markdown():
    return """---
Title: Test Law
Jurabk: TestG
---

# Test Law

# § 1 Scope
This is the first paragraph.
It has multiple lines.

# § 2 Details
(1) First absatz.
(2) Second absatz.
$$3$$
(3) Third absatz with marker.
"""
