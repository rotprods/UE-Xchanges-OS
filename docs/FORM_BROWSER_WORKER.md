# UE-Xchanges Form Browser Worker v1

## Purpose

The Browser Worker is a thin local actuator around the existing Form Execution Gateway. It does not own eligibility, application state, AI policy, evidence truth, approval, receipt authority or Submit.

It keeps one dedicated Chromium profile and one live browser context available to a local execution client while exposing only a small typed HTTP surface.

## Security boundary

```text
HTTP bind                  loopback only
browser target scope       loopback only in v1
/v1 bearer token           mandatory
CORS                        absent
cross-site Origin           denied
cross-site Sec-Fetch-Site   denied
Host                        must resolve to loopback
body limit                  1 MB
POST                         X-UEX-Request-ID required
concurrency                  serialized single-flight
popups                       closed
form Submit                  blocked in page runtime
```

The token comes only from `UEX_BROWSER_WORKER_TOKEN`, must be at least 32 non-whitespace characters and must never be committed, persisted in Drive/Notion or pasted into ChatGPT.

The worker exposes no cookie, storage-state, password or OTP APIs.

## Why Browser Worker v1 is loopback-target-only

The repository currently certifies zero external PREFILL providers. Browser Worker v1 therefore also refuses external INSPECT targets instead of creating a hidden bypass around provider certification.

INSPECT, PREFILL and VALIDATE all use loopback fixture targets and same-origin GET/HEAD/OPTIONS networking only. Cross-origin requests and mutating HTTP methods are blocked.

A later provider-certification PR may deliberately raise the target ceiling after Runtime Attestation + Authenticated INSPECT + Provider Manifest evidence exists.

## Protocol

### `GET /healthz`

Unauthenticated liveness only:

```json
{"ok":true,"status":"ok"}
```

### `GET /v1/status`

Requires bearer auth. Returns worker mode, browser channel, opaque profile hash, current value-free form identity, busy state and exact operation set.

### `POST /v1/inspect`

```json
{
  "provider": "generic_html",
  "url": "http://127.0.0.1:39000/form",
  "allowed_origins": ["http://127.0.0.1:39000"]
}
```

The target and every allowed origin must resolve to the same loopback origin. Output contains structure, `form_fingerprint`, `validation_signature` and safety flags, never current field values, cookies or storage state.

The worker retains internally:

- canonical target URL;
- safe page URL without query/fragment material;
- form fingerprint;
- validation signature;
- validation expectation;
- current application ID after prefill.

### `POST /v1/prefill-local`

Disabled by default. Explicit local-development gate:

```bash
export UEX_BROWSER_WORKER_ALLOW_LOCAL_PREFILL=1
```

The existing `validateLocalPrefillPlan()` policy remains authoritative: non-loopback targets, unresolved/BLACK fields, attachments, unsupported editable fields and expired plans are rejected.

There is no external PREFILL endpoint in v1.

### `POST /v1/validate-local`

Validation executes against the same live page retained by the Browser Worker, so PREFILL state is not lost between separate Chromium processes. Reports contain field keys and booleans only, never values.

## Request idempotency

Every POST requires `X-UEX-Request-ID`.

```text
request_id -> SHA256(raw body) + cached response
```

- same ID + same body → cached response with `X-UEX-Replayed: 1`;
- same ID + different body → HTTP 409;
- cache is bounded and in-memory only.

This is transport idempotency. Submission idempotency remains owned by canonical `SubmissionAttempt` / receipt logic.

## Human login

Human takeover remains outside the HTTP worker in v1. Use the existing target-Mac activation flow:

```bash
npm run activate -- human-login ...
```

This preserves the TTY/human-presence requirement for username/password/SSO/2FA/CAPTCHA. The worker can later reuse the same dedicated profile; it never receives those secrets.

## Start

```bash
cd services/browser-worker
npm install --ignore-scripts --no-audit --no-fund --package-lock=false
export UEX_BROWSER_WORKER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export UEX_BROWSER_CHANNEL=chrome
export UEX_BROWSER_HEADLESS=0
npm start
```

Expected:

```text
UEX_BROWSER_WORKER_READY http://127.0.0.1:4777
UEX_BROWSER_WORKER_SUBMIT_ENDPOINT=ABSENT
```

## Remote-control architecture

Never bind the worker to `0.0.0.0` and never expose it directly to the public Internet.

```text
Agent / RuntimeGraph
       ↓ typed capability request
future authenticated local relay / MCP
       ↓ loopback
UEX Browser Worker
       ↓
Dedicated Chromium profile
```

Cross-host transport is deliberately a separate future component with its own authentication and threat model.

## Current capability ceiling

```text
status             YES
inspect-loopback   YES
prefill-local      YES only when explicitly enabled
validate-local     YES
human login        local CLI only
external inspect   NO
external prefill   NO
submit             NO
upload             NO
payment            NO
cookies export     NO
storage export     NO
```

Provider certification must happen before any external browser target capability is added.
