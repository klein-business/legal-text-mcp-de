# Build a federal dataset from official sources

- Use the current source checkout; this includes the fix for empty repealed norms after v2.1.3.
- Scope: the nine federal laws registered in `SOURCE_SPECS` — BGB, EGBGB, DDG, UWG, TDDDG, BDSG, BFSG, VSBG, PAngV.
- This is a selected dataset, not a complete federal-law corpus. No EU or state laws are included.
- Public corpus OCI references and the `-full` image currently return `DENIED`. Whether those packages are private or absent is [UNVERIFIED].
- `prepare_data.build_corpus --sources bund` is not implemented; its `.tar.zst` output is not the directory format used by the serving runtime.

## Build and validate

```bash
uv sync --locked --all-groups
uv run python - <<'PY'
import json
from pathlib import Path
from legal_text_mcp_de.legal_texts.importer import default_fetch, source_metadata, utc_now
from legal_text_mcp_de.legal_texts.sources import SOURCE_SPECS
from legal_text_mcp_de.legal_texts.normalizer import normalize_snapshot
from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.search import SearchService
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.config import Settings
root = Path("federal-corpus")
raw = root / "raw"
raw.mkdir(parents=True, exist_ok=False)
entries = []
for law_id, spec in SOURCE_SPECS.items():
    if spec.source_kind != "gesetze-im-internet":
        continue
    status, headers, body = default_fetch(spec.source_url)
    if status != 200:
        raise RuntimeError(f"{law_id}: HTTP {status}")
    path = raw / f"{law_id}.zip"
    path.write_bytes(body)
    entries.append({"canonical_id": law_id, "raw_path": str(path.resolve()), "source": source_metadata(spec, body, utc_now())})
    print(law_id, len(body), flush=True)
manifest = raw / "manifest.json"
manifest.write_text(json.dumps({"entries": entries}), encoding="utf-8")
dataset_dir = root / "dataset"
print(normalize_snapshot(manifest, dataset_dir))
SearchService(NormalizedDataset.load(dataset_dir)).write_index_marker()
runtime = LegalTextRuntime.from_settings(Settings(dataset_path=str(dataset_dir)))
print(runtime.readiness())
print("BGB norms", len(runtime.get_law("BGB")["norms"]))
print("BGB § 1", runtime.get_norm("BGB", "§ 1")["norm"]["text"])
print("search hits", runtime.search_laws("Rechtsfähigkeit", ["BGB"])["count"])
PY
```

- The command creates `federal-corpus/raw` and `federal-corpus/dataset`; it refuses to reuse an existing raw directory.
- Each download retains its official URL, retrieval timestamp, and content hash.
- A failed fetch or validation stops the command. Start serving only after all checks succeed.
- The source snapshot tested on 2026-10-09 yielded 9 laws and 3,308 norm records; future upstream snapshots may differ.
- Coverage here means runtime parsing and availability, not a legal completeness audit of each source.

## Serve from the same checkout

```bash
DATASET_PATH="$PWD/federal-corpus/dataset" HOST=127.0.0.1 uv run legal-text-mcp-de http
```

Keep the server running. In a second terminal:

```bash
curl --fail http://localhost:8001/ready
curl --fail http://localhost:8001/laws/BGB
```

## Docker sidecar

```bash
docker build -t legal-text-mcp-de:local .
docker run --rm -p 127.0.0.1:8001:8001 \
  -v "$PWD/federal-corpus/dataset:/data/legal-texts:ro" \
  legal-text-mcp-de:local \
  uv run --frozen --no-sync legal-text-mcp-de http
```

- Build the image from the same checkout: published v2.1.3 lacks the repealed-norm validation fix.
- `/health` confirms process liveness. Require `/ready` before sending data requests.
