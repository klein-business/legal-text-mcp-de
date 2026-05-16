# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from legal_texts.sources import SOURCE_SPECS


def test_required_sources_are_encoded():
    assert SOURCE_SPECS["egbgb"].source_identifier == "bgbeg"
    assert SOURCE_SPECS["tdddg"].source_identifier == "ttdsg"
    assert SOURCE_SPECS["pangv_2022"].source_identifier == "pangv_2022"
    assert SOURCE_SPECS["dsgvo_eu_2016_679"].metadata["document"] == "DOC_2"
    assert SOURCE_SPECS["dsgvo_eu_2016_679"].metadata["expression"] == "0004.02"


def test_known_invalid_alias_paths_are_regression_cases():
    invalid_urls = [url for spec in SOURCE_SPECS.values() for url in spec.invalid_urls]
    assert "https://www.gesetze-im-internet.de/tddsg/index.html" in invalid_urls
    assert "https://www.gesetze-im-internet.de/pangv/index.html" in invalid_urls
