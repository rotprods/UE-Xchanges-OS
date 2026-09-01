# UE-Xchanges Form Browser Worker v1

## Purpose

The Browser Worker is a thin local actuator around the existing Form Execution Gateway. It does not own eligibility, application state, AI policy, evidence truth, approval, receipt authority or Submit.

It exists to keep one dedicated Chromium profile and one live browser context available to a local execution client while exposing only a small typed HTTP surface.

## Security boundary

The worker is intentionally local-only:

```text
bind = 127.0.0.1 / loopback only
bearer token = required for every /v1 endpoint
CORS = absent
cross-site Origin = denied
cross-site Sec-Fetch-Site = denied
Host must resolve to loopback
request body <= 1 MB
POST requires X-UEX-Request-ID
operations serialized single-flight
```

The token is read only from `UEX_BROWSER_WORKER_TOKEN` and must be at least 32 non-whitespace characters. Never commit it, store it in Drive/Notion, or paste it into ChatGPT.

The worker never exposes cookie, storage-state, password or OTP APIs.

## Protocol

### Unauthenticated liveness

```http
GET /healthz
```

Returns only:

```json
{"ok":true,"status":"ok"}
```

### Authenticated status

```http
GET /v1/status
Authorization: Bearer <local-secret>
```

Returns worker mode, browser channel, opaque profile hash, current value-free form identity and the exact operation set.

### INSPECT

```http
POST /v1/inspect
Authorization: Bearer <local-secret>
X-UEX-Request-ID: <unique-id>
Content-Type: application/json

{
  "provider": "generic_html",
  "url": "https://provider.example/form",
  "allowed_origins": ["https://provider.example"]
}
```

INSPECT uses the existing mutation-blocking Form Gateway guards. It may observe public/authenticated form structure but never reads current field values, cookies or storage state.

It stores internally:

- canonical target URL;
- form fingerprint;
- validation signature;
- validation expectation;
- safe page URL without query/fragment material.

### PREFILL_LOCAL

```http
POST /v1/prefill-local
```

This endpoint is disabled by default and exists only for loopback fixture development. Enable explicitly with:

```bash
export UEX_BROWSER_WORKER_ALLOW_LOCAL_PREFILL=1
```

The existing `validateLocalPrefillPlan()` policy remains authoritative: non-loopback targets, unresolved/BLACK fields, attachments, unsupported fields and expired plans are rejected.

There is no external PREFILL endpoint in v1.

### VALIDATE_LOCAL

```http
POST /v1/validate-local
```

Validation runs against the same live page retained by the Browser Worker. This proves that PREFILL and validation no longer lose DOM state between separate Chromium processes.

Reports contain field keys and booleans only, not field values.

## Idempotency

Every POST requires `X-UEX-Request-ID`.

The worker stores a bounded in-memory map:

```text
request_id -> SHA256(raw request body) + response
```

Same ID + same body returns the cached response with:

```http
X-UEX-Replayed: 1
```

Same ID + different body returns HTTP 409.

This is transport idempotency only. Submission idempotency remains owned by the canonical SubmissionAttempt/Receipt engine.

## Human login

Human takeover remains deliberately outside the HTTP worker in v1.

Use the existing local activation command:

```bash
npm run activate -- human-login ...
```

This preserves the TTY/human-presence gate for username/password/SSO/2FA/CAPTCHA.

The worker may then reuse the same dedicated browser profile after the local human login has completed.

## Start

From `services/browser-worker`:

```bash
npm install --ignore-scripts --no-audit --no-fund --package-lock=false
export UEX_BROWSER_WORKER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export UEX_BROWSER_CHANNEL=chrome
export UEX_BROWSER_HEADLESS=0
npm start
```

Expected output:

```text
UEX_BROWSER_WORKER_READY http://127.0.0.1:4777
UEX_BROWSER_WORKER_SUBMIT_ENDPOINT=ABSENT
```

## Remote-control architecture

Do **not** bind this worker to `0.0.0.0` and do not expose it directly to the public Internet.

The intended future topology is:

```text
Agent / RuntimeGraph
       ↓ typed capability request
Authenticated local relay / MCP
       ↓ loopback
UEX Browser Worker
       ↓
Dedicated Chromium profile
```

Cross-host transport must be a separate authenticated relay with its own threat model. The Browser Worker itself remains loopback-only.

## Current capability ceiling

```text
status          YES
inspect         YES
prefill-local   YES only when explicitly enabled
validate-local  YES
human login     local CLI only
external prefill NO
submit           NO
upload           NO
payment          NO
cookies export   NO
storage export   NO
```

A future external PREFILL capability must still pass the Runtime Attestation + Authenticated INSPECT + Provider Capability Manifest + Plan Identity v2 promotion gate before any worker endpoint is added.
