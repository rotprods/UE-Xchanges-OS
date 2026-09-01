# UE-Xchanges Local Browser Stack Supervisor v1

## Objective

Turn the Form Execution Gateway into a one-command local MCP stack without making the human or an MCP host manually coordinate Worker URLs, bearer tokens, Relay processes or shutdown order.

```text
MCP Host
   ↓ stdio
Browser Stack Supervisor
   ├── generates Worker bearer in memory only
   ├── loads/creates local PREFILL authorization key (0600)
   ├── starts Browser Worker on random loopback port
   ├── waits exact readiness marker
   ├── starts Browser Relay with inherited MCP stdio
   └── kills Relay + Worker together on close/signal
             ↓
       Browser Relay MCP
             ↓ bearer loopback HTTP
       Browser Worker
             ↓
       Dedicated Chromium profile
```

The supervisor never parses or proxies MCP messages. Relay stdout inherits the supervisor stdout file descriptor directly; supervisor runtime messages go to stderr only.

## Secrets

### Worker bearer

Generated from 48 random bytes every supervisor start.

```text
persisted to disk: NO
returned in MCP: NO
logged: NO
passed to Worker: YES, child env only
passed to Relay: YES, child env only
```

When the supervisor stops, the bearer disappears with the processes.

### PREFILL capability signing key

The signing key must survive long enough for a local human/RuntimeGraph authorization command to issue short-lived plan-bound capabilities.

Default location:

```text
~/.uexchanges/secrets/browser-relay-capability.key
```

Properties:

```text
parent directory: 0700
key file:         0600
symlinks:         rejected
outside managed root: rejected
```

The key value is never printed or returned through MCP.

## Child environment minimization

Worker and Relay do **not** inherit the full parent environment.

Only selected system variables may cross the boundary, such as:

```text
HOME
PATH
TMPDIR / TMP / TEMP
LANG / LC_ALL
DISPLAY
XDG_RUNTIME_DIR
DBUS_SESSION_BUS_ADDRESS
PLAYWRIGHT_BROWSERS_PATH
```

Secrets such as `GITHUB_TOKEN`, cloud API keys or unrelated connector credentials are not forwarded.

The supervisor then explicitly adds only the required UEX Worker/Relay credentials.

## One-time dependency bootstrap

From the repository root:

```bash
npm --prefix services/browser-stack install --ignore-scripts --no-audit --no-fund --package-lock=false
npm --prefix services/browser-relay install --ignore-scripts --no-audit --no-fund --package-lock=false
npm --prefix services/browser-worker install --ignore-scripts --no-audit --no-fund --package-lock=false
npx --prefix services/browser-worker playwright install chromium
```

For Chrome channel usage on macOS, Chrome itself must also be installed.

## Doctor

```bash
npm --prefix services/browser-stack run doctor -- --channel chrome
```

The doctor verifies:

- Node >= 20;
- Worker Playwright dependency installed;
- Relay MCP dependency installed;
- Browser Worker doctor launches the requested browser;
- Browser Worker doctor networking is blocked;
- capability secret path is private and managed;
- Worker bearer persistence is `memory_only`;
- Submit capability is `false`.

The doctor may create the local signing key if it does not exist. It never prints the key value.

## MCP host command

The MCP host only needs to start one executable:

```text
node /absolute/path/UE-Xchanges-OS/services/browser-stack/src/server.mjs
```

No Worker token or Relay signing secret needs to be written into the host's MCP configuration.

Optional non-secret runtime configuration:

```text
UEX_BROWSER_CHANNEL=chrome
UEX_BROWSER_HEADLESS=0
UEX_BROWSER_STACK_ALLOW_LOCAL_PREFILL=0
```

`UEX_BROWSER_STACK_ALLOW_LOCAL_PREFILL` defaults to false.

## Local PREFILL authorization

PREFILL remains capability-gated even when the supervisor is running.

To issue a short-lived capability for one exact request ID and plan:

```bash
npm --prefix services/browser-stack run capability -- \
  --request-id req-prefill-0001 \
  --plan ~/.uexchanges/activation/plan.json \
  --out ~/.uexchanges/activation/prefill.cap \
  --ttl 120
```

The CLI:

- reads the managed local signing key;
- hashes canonical `{plan}`;
- binds request ID + plan hash + expiry;
- writes the capability file mode 0600;
- never prints the token.

Changing one plan value or request ID invalidates the capability.

The capability is not a password or browser credential. It authorizes one short-lived local PREFILL operation only.

## Human login

Human login remains the existing TTY/browser takeover flow and should normally happen before the MCP supervisor starts, because Chromium persistent profiles must not be opened concurrently by two processes.

```bash
npm --prefix tools/form-executor run activate -- human-login ...
```

The human enters username/password/SSO/2FA/CAPTCHA directly in visible Chrome. Those values never enter the supervisor or MCP relay.

After login finishes, start the Browser Stack and it can reuse the same dedicated profile.

## Current target ceiling

Browser Worker v1 remains intentionally loopback-target-only:

```text
status             YES
inspect-local      YES
validate-local     YES
prefill-local      YES only if Worker start gate + HMAC capability both pass
external inspect   NO
external prefill   NO
submit             NO
upload             NO
payment            NO
cookie export      NO
storage export     NO
```

The supervisor does not raise that ceiling.

## CI acceptance

`browser-stack.yml` installs Stack + Relay + Worker dependencies and Chromium, then runs:

1. Stack doctor.
2. Unit security tests.
3. A real MCP `StdioClientTransport` that launches **only the supervisor**.
4. The client lists the four Relay tools through the supervisor.
5. `browser_status` proves the Worker is live and Submit absent.
6. Client closes MCP.
7. Test confirms the Worker `/healthz` port becomes unavailable.

This proves process ownership and cleanup end-to-end, not merely module-level correctness.

## Future promotion

The next safe capability wave after this supervisor is **provider certification**, not Submit.

For one real provider:

```text
human login
→ runtime attestation
→ authenticated INSPECT evidence
→ provider-specific adapter/manifest
→ adversarial live PREFILL dry run
→ value-free validation
→ provider manifest PREFILL certification
```

Submit remains an independent later capability with ApprovalToken + receipt requirements.
