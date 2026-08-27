# Source Access Matrix — verified 2026-08-27

The discovery layer must model how each provider actually exposes data. A zero-result parser is not considered a successful collector.

| Source | Access mode | v0.1 strategy |
|---|---|---|
| SALTO European Training Calendar | public static paginated HTML | deterministic index scan with `b_offset` / `b_limit`, content hashes and detail URL dedupe |
| SALTO Calls for Trainers | auth-required index, public detail pages | never bypass login; ingest public call URLs from authorised/search-backed discovery and watch known organiser pages |
| European Youth Portal ESC opportunities | dynamic index shell | browser/API/search-backed discovery; deterministic processing begins once a public detail URL is obtained |
| Eurodesk Opportunity Finder | dynamic/query-driven | query/browser/search-backed discovery; deterministic URL/provenance/dedupe after discovery |

## Contract

Dynamic/auth sources are not silently downgraded to generic HTML scraping. Each run must report `access_mode`, `blocked_reason` where applicable, and the discovery method/provenance for externally supplied candidate URLs.

## Incremental state

`SourceStateStore` persists ETag, Last-Modified, content hash, last fetch/change timestamps and candidate fingerprints. SQLite is intentional for the single-operator v1; Postgres/Supabase is deferred until multi-process/remote persistence becomes a real requirement.
