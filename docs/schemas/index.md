# JSON Schemas

- Source: `src/legal_text_mcp_de/http_models.py`.
- Regenerate: `uv run python scripts/export_json_schemas.py`.
- CI rejects changed, missing, or newly generated schemas that were not committed.
- HTTP responses use these shapes directly; CLI success envelopes wrap the response in `data`.
- These contracts preserve the models' flexible nested dictionaries; they do not add validation absent from the runtime.

| Schema | Contract |
| --- | --- |
| [HealthResponse](HealthResponse.schema.json) | Process health status |
| [ReadinessResponse](ReadinessResponse.schema.json) | Dataset readiness and details |
| [ErrorBody](ErrorBody.schema.json) | Error code, message, details, and optional source |
| [ErrorResponse](ErrorResponse.schema.json) | HTTP error envelope |
| [LawListResponse](LawListResponse.schema.json) | Law list, count, and optional query |
| [LawDetailResponse](LawDetailResponse.schema.json) | Law metadata and norms |
| [CitationResponse](CitationResponse.schema.json) | Resolved norm, citation, and provenance |
| [SearchResponse](SearchResponse.schema.json) | Query, search hits, and count |
| [SourceMetadataResponse](SourceMetadataResponse.schema.json) | Source metadata list |
| [CorpusCoverageResponse](CorpusCoverageResponse.schema.json) | Package coverage and source counts |
| [SourceLimitationsResponse](SourceLimitationsResponse.schema.json) | Source limitations and filters |
| [RelationshipsResponse](RelationshipsResponse.schema.json) | Norm relationships |
| [FlexibleModel](FlexibleModel.schema.json) | Shared base allowing extra fields |
