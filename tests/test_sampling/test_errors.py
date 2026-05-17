# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from legal_text_mcp_de.sampling.errors import (
    SamplingError,
    SamplingNotSupported,
    SamplingRefused,
    SamplingTimeout,
    SchemaValidationError,
)


def test_all_specific_errors_subclass_sampling_error():
    for cls in (SamplingNotSupported, SamplingTimeout, SamplingRefused, SchemaValidationError):
        assert issubclass(cls, SamplingError)
