---
type: documentation
entity: module
module: "data-preparation"
version: 2.0
---

# Module: data-preparation

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `prepare_data/` directory contains the v2 corpus build pipeline and the
legacy `gesetze-tools` helper. The v2 pipeline is the production path for
generating the signed `.tar.zst` corpus bundle that the server loads at startup.

### Responsibility

This module is responsible for:

- scraping German state-law portals (Bayern, NRW, BW, NDS, Hessen);
- fetching EU acts from the EUR-Lex Cellar SPARQL endpoint (ePrivacy, DSA, DMA, AI Act);
- normalising all scraped content to the runtime dict shape;
- packing normalised laws into a versioned, zstandard-compressed `.tar.zst` bundle;
- the `build_corpus` CLI entrypoint that orchestrates source selection and packing.

The legacy `prepare_gesetze_im_internet.sh` helper remains for manual
Markdown-era experimentation and is not the production source path.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `SPARQLWrapper` | library | SPARQL queries against the EUR-Lex Cellar endpoint. |
| `beautifulsoup4` / `types-beautifulsoup4` | library | HTML parsing for state-law portal pages. |
| `zstandard` | library | Zstandard compression for the `.tar.zst` bundle. |
| `legal_text_mcp_de.corpus.bundle_schema` | internal | `BundleManifest` and `BundleEntry` models. |
| `git`, `uv` | CLI tools | Legacy helper (not the production path). |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `prepare_data/build_corpus.py` | file | CLI entrypoint: `python -m prepare_data.build_corpus --output corpus.tar.zst --sources bund,land:by,eu:32016R0679`. |
| `prepare_data/bundle_packager.py` | file | `pack_bundle` — writes a zstandard `.tar.zst` with `manifest.json` + `laws/<id>.json`. |
| `prepare_data/normalizer.py` | file | `normalize_for_runtime` — converts scraper output to the runtime dict shape. |
| `prepare_data/lawde_wrapper.py` | file | Wrapper around the `lawde` CLI for federal GII law download. |
| `prepare_data/state_law/base.py` | file | `StateLawScraper` abstract base class: `fetch_index`, `fetch_law`, `normalize`. |
| `prepare_data/state_law/bayern.py` | file | `BayernStateLaw` scraper. |
| `prepare_data/state_law/nrw.py` | file | `NRWStateLaw` scraper. |
| `prepare_data/state_law/bw.py` | file | `BWStateLaw` scraper. |
| `prepare_data/state_law/nds.py` | file | `NDSStateLaw` scraper. |
| `prepare_data/state_law/he.py` | file | `HEStateLaw` scraper. |
| `prepare_data/eu_acts/cellar_client.py` | file | SPARQL client for the EUR-Lex Cellar endpoint. |
| `prepare_data/eu_acts/eprivacy.py` | file | `EPrivacyAct` loader (CELEX `32002L0058`). |
| `prepare_data/eu_acts/dsa.py` | file | `DSAAct` loader (CELEX `32022R2065`). |
| `prepare_data/eu_acts/dma.py` | file | `DMAAct` loader (CELEX `32022R1925`). |
| `prepare_data/eu_acts/ai_act.py` | file | `AIAct` loader (CELEX `32024R1689`). |
| `prepare_data/eu_acts/_normalize.py` | file | Shared normalisation helpers for EU-act Cellar XML. |
| `prepare_data/prepare_gesetze_im_internet.sh` | file | Legacy helper script for `gesetze-tools`. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `pack_bundle` | function | `bundle_packager.py` | Writes a `.tar.zst` bundle and returns the `BundleManifest`. |
| `normalize_for_runtime` | function | `normalizer.py` | Converts scraper law dicts to the `NormalizedDataset`-compatible shape. |
| `BayernStateLaw` / `NRWStateLaw` / `BWStateLaw` / `NDSStateLaw` / `HEStateLaw` | classes | `state_law/*.py` | State-law scrapers. |
| `EPrivacyAct` / `DSAAct` / `DMAAct` / `AIAct` | classes | `eu_acts/*.py` | EU-act Cellar loaders. |

## Usage

```bash
python -m prepare_data.build_corpus \
    --output corpus.tar.zst \
    --sources bund,land:by,land:nrw,land:bw,land:nds,land:he,eu:32016R0679
```

Source spec syntax:

- `bund` — federal laws via `lawde` (stub in v2.0; full integration deferred)
- `land:<code>` — state law; codes: `by`, `nrw`, `bw`, `nds`, `he`
- `eu:<celex>` — EU act by CELEX number

## Bundle Layout

The output `.tar.zst` contains:

```
manifest.json           — BundleManifest JSON (schema_version=2)
laws/<canonical_id>.json — one file per law
```

## Validation

The legacy helper supports a no-network dependency check:

```bash
prepare_data/prepare_gesetze_im_internet.sh --dry-run
```

## Production Boundary

The production container loads corpus bundles built by `build_corpus` and
distributed as OCI artifacts from GHCR. The state-law scrapers and EU-act loaders
in this module are the upstream source of those bundles. The legacy
`prepare_gesetze_im_internet.sh` path is not used in the production pipeline.

## Inventory Notes

- **Coverage**: v2 scrapers and `pack_bundle` are covered by unit tests with
  mocked HTTP responses. End-to-end scraper runs are network-gated and not part
  of ordinary PR CI.
- **Notes**: Keep `prepare_data/` clearly separated from the server runtime.
  Nothing in `prepare_data/` is imported by `src/legal_text_mcp_de/` at server
  startup time.
