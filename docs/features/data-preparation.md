---
type: documentation
entity: feature
feature: "data-preparation"
version: 2.0
---

# Feature: data-preparation

> Part of [legal-text-mcp-de](../overview.md)

## Summary

v2 adds a full corpus build pipeline in `prepare_data/`. The `build_corpus` CLI
scrapes German state-law portals and the EUR-Lex Cellar, then packs the result
into a signed `.tar.zst` bundle that the server loads directly. The v1
importer/normalizer workflow remains for fixture and development use.

## v2 Corpus Build Workflow

```bash
python -m prepare_data.build_corpus \
    --output corpus.tar.zst \
    --sources bund,land:by,land:nrw,land:bw,land:nds,land:he,eu:32016R0679
```

1. `build_corpus` parses `--sources` into source-type/code pairs.
2. State-law scrapers (`BayernStateLaw`, `NRWStateLaw`, `BWStateLaw`,
   `NDSStateLaw`, `HEStateLaw`) fetch law indexes and full texts from official
   state portals.
3. EU-act loaders (`EPrivacyAct`, `DSAAct`, `DMAAct`, `AIAct`) query the EUR-Lex
   Cellar SPARQL endpoint and parse Formex/XML.
4. `normalize_for_runtime` converts all scraper output to the `NormalizedDataset`-
   compatible dict shape.
5. `pack_bundle` writes a zstandard-compressed `.tar.zst` with `manifest.json`
   and one `laws/<id>.json` per law (schema_version=2).
6. The bundle is published as an OCI artifact to GHCR and signed with cosign.
7. The production server loads the bundle via `corpus/loader.py` at startup.

## v1 Reliable Data Workflow

The v1 importer/normalizer workflow is retained for fixtures and CI:

1. Use source specs from `src/legal_text_mcp_de/legal_texts/sources.py`.
2. Probe and download official source artifacts with `legal_texts/importer.py`.
3. Persist raw artifacts and manifests with SHA-256 hashes.
4. Normalize with `legal_texts/normalizer.py`.
5. Validate the serving package with `legal_texts/validation.py`.
6. Start MCP/HTTP with `DATASET_PATH` pointing at the normalized package.

## Legacy Helper

`prepare_data/prepare_gesetze_im_internet.sh` still exists for manual
Markdown-era experimentation through `gesetze-tools`. Its output is not a
production source for the supported runtime.

## Related

- [data-preparation module](../modules/data-preparation.md)
- [law-loading-and-indexing](law-loading-and-indexing.md)
- [source-provenance](source-provenance.md)
- [corpus module](../modules/corpus.md)
