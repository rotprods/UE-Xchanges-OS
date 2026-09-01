# UE-Xchanges Browser Relay MCP v1

## Purpose

The Browser Relay is the local capability boundary between an MCP host/agent and the loopback Browser Worker.

```text
MCP Host / RuntimeGraph
        ↓ stdio
UEX Browser Relay
        ↓ bearer-authenticated loopback HTTP
UEX Browser Worker
        ↓
Dedicated Chromium profile
```

The relay does **not** own Chromium, cookies, passwords, OTPs, storage state, application truth, eligibility, approval, receipts or Submit.

## MCP transport

The relay uses MCP TypeScript SDK v2 and **stdio only**. stdout is reserved for MCP JSON-RPC; runtime diagnostics use stderr only.

No Streamable HTTP/SSE/WebSocket MCP transport is implemented in v1.

## MCP tools

The complete v1 surface is:

```text
browser_status
browser_inspect_local
browser_validate_local
browser_prefill_local
```

There is no tool for:

```text
Submit
external inspect
external prefill
cookies
storage state
password / OTP
shell / arbitrary JS
eval
upload
payment
```

`browser_inspect_local` and `browser_validate_local` are value-free operations over the existing loopback-only Browser Worker.

`browser_prefill_local` is a DOM mutation and therefore requires a short-lived HMAC capability.

## Relay secrets

The relay process receives two local environment secrets:

```text
UEX_BROWSER_WORKER_TOKEN
UEX_BROWSER_RELAY_CAPABILITY_SECRET
```

Optional worker URL:

```text
UEX_BROWSER_WORKER_URL=http://127.0.0.1:4777/
```

The worker URL validator accepts loopback HTTP only. The worker token and capability secret are never returned in MCP tool results.

Do not put either secret in GitHub, Drive, Notion, Todoist, MCP tool arguments or chat.

## PREFILL capability

A capability is domain-separated HMAC data:

```text
operation = prefill-local
request_id
SHA256(canonical {plan})
issued_at
expires_at
nonce
```

Maximum TTL: 300 seconds.

The exact plan and request ID supplied to `browser_prefill_local` must match the signed capability. Changing one answer, application ID, fingerprint, validation signature or request ID invalidates the capability before the Worker is called.

Capability issuance is a **local CLI**, not an MCP tool:

```bash
cd services/browser-relay
export UEX_BROWSER_RELAY_CAPABILITY_SECRET='...local secret...'

npm run capability -- \
  --request-id req-prefill-0001 \
  --plan ~/.uexchanges/activation/plan.json \
  --out ~/.uexchanges/activation/prefill.cap \
  --ttl 120
```

The token file is written mode `0600`. The CLI reports only path/body-hash metadata and does not print the token.

A future RuntimeGraph/approval component may issue the same capability after provider/plan gates pass. The MCP relay itself cannot self-authorize a write.

## Start local stack

### Browser Worker

```bash
cd services/browser-worker
npm install --ignore-scripts --no-audit --no-fund --package-lock=false
export UEX_BROWSER_WORKER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export UEX_BROWSER_CHANNEL=chrome
export UEX_BROWSER_HEADLESS=0
npm start
```

The worker stays bound to loopback.

### MCP relay

In another local environment/process with the same worker token:

```bash
cd services/browser-relay
npm install --ignore-scripts --no-audit --no-fund --package-lock=false
export UEX_BROWSER_RELAY_CAPABILITY_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export UEX_BROWSER_WORKER_URL='http://127.0.0.1:4777/'
node src/server.mjs
```

Normally an MCP host launches `node src/server.mjs` itself over stdio. Do not manually pipe ordinary logs to stdout.

## Host configuration principle

Configure the MCP host to run the relay command locally and inherit secrets from a local secret-managed environment. Avoid committing secrets inside MCP configuration files.

Conceptually:

```json
{
  "command": "node",
  "args": ["/absolute/path/UE-Xchanges-OS/services/browser-relay/src/server.mjs"]
}
```

Exact host-specific configuration belongs outside this repository if it would contain secret values.

## End-to-end CI proof

The dedicated `browser-relay` workflow installs:

- Node 22;
- MCP server/client v2.0.0;
- Zod 4.5.4;
- Browser Worker dependencies;
- Playwright 1.62.1 + Chromium.

It executes:

```text
MCP Client
  → InMemory MCP transport
  → Browser Relay tools
  → bearer-authenticated loopback Worker
  → one persistent Chromium DOM
  → INSPECT_LOCAL
  → HMAC capability
  → PREFILL_LOCAL
  → VALIDATE_LOCAL
```

The fixture simultaneously attempts POST telemetry and form `requestSubmit()`; zero mutation may reach the fixture server.

CI also asserts no forbidden MCP tool names and no `console.log` in relay source.

## Separation from Submit

Transport-level PREFILL capability does not authorize Submit.

Future Submit still requires the canonical independent chain:

```text
Plan Identity v2
+ fresh form fingerprint
+ fresh validation signature
+ hard gates PASS
+ Human ApprovalToken
+ duplicate guard PASS
+ SubmissionAttempt persisted before click
+ separately certified provider Submit capability
+ confirmation evidence
+ durable receipt
= SUBMITTED_CONFIRMED
```

Browser Relay v1 contains no implementation of that action.
