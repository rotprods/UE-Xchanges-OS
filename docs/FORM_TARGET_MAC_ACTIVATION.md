# Target-Mac Form Activation Compiler

## Status

This runbook activates **evidence generation only** on the target Mac.

It does not certify an external provider, enable external PREFILL, click Submit, upload a file, make a payment, read/export cookies, export storage state, or capture passwords/OTP.

The activation chain is:

```text
browser doctor
  -> canonical doctor evidence
  -> signed runtime attestation
  -> HUMAN_LOGIN_TAKEOVER
  -> opaque human-login evidence
  -> value-free authenticated INSPECT
  -> signed INSPECT evidence
  -> provider manifest candidate (NOT certified)
  -> pure PREFILL promotion check
```

A positive promotion check is still only a decision/hash. It does not execute browser writes.

## Security invariants

1. Run this only from the dedicated `UE-Xchanges-OS` repository checkout.
2. Use a dedicated UEX browser profile, never a personal Chrome/Chromium/Edge profile.
3. Keep activation artifacts outside Git and with mode `0600`.
4. Runtime and INSPECT HMAC secrets exist only in the local process environment or a future local secret store.
5. Never paste those secrets, the runtime token, the INSPECT token, passwords, OTPs, cookies or browser storage into ChatGPT, GitHub, Drive, Todoist or Slack.
6. HUMAN_LOGIN_TAKEOVER is performed by the human in the visible browser. The agent does not read the page during login.
7. The initial login URL must be a base HTTP(S) URL without query or fragment material.
8. INSPECT may compute `form_fingerprint` and `validation_signature` in memory but exports no answer values, query material, cookies or storage state.
9. `provider-candidate` always emits `prefill_certified=false` and `submit_certified=false`.
10. Current repository policy still has zero external PREFILL-certified providers and zero Submit-certified providers.

## Prerequisites

From repository root:

```bash
cd UE-Xchanges-OS/tools/form-executor
npm install --ignore-scripts --no-audit --no-fund --package-lock=false
```

Use Node 20+ and Python 3.11+.

Create a private local activation directory:

```bash
umask 077
mkdir -p ~/.uexchanges/activation
mkdir -p ~/.uexchanges/browser/profile
```

`~/.uexchanges/browser/profile` is a dedicated UEX profile. Do not point the tooling at your normal browser profile.

## 1. Run the canonical doctor

From `tools/form-executor`:

```bash
npm run activate -- doctor \
  --channel chrome \
  --out ~/.uexchanges/activation/doctor.json
```

Required doctor state:

```text
status = ok
Node major >= 20
Playwright = installed version
browser channel = chrome | chromium | msedge
launch = ok
network = blocked
profile = ephemeral
```

The compiler rejects extra doctor fields and ambiguous types.

## 2. Create local HMAC secrets

Generate the secrets directly into environment variables. Do not print or paste them elsewhere.

```bash
export UEX_RUNTIME_ATTESTATION_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export UEX_INSPECT_ATTESTATION_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
```

For a long-lived installation, replace this temporary environment approach with a local OS secret-store workflow. Do not commit `.env` files containing these values.

## 3. Issue the runtime attestation

```bash
npm run activate -- attest-runtime \
  --doctor ~/.uexchanges/activation/doctor.json \
  --runtime-ref runtime:uex-primary-mac \
  --out ~/.uexchanges/activation/runtime.attestation
```

Default TTL: 4 hours.

The output file is mode `0600`. Console output contains only safe metadata such as attestation ID, versions and expiry; it does not print the token or signing secret.

## 4. HUMAN_LOGIN_TAKEOVER

Use the provider's **base login URL without query or fragment**.

Example shape only:

```bash
npm run activate -- human-login \
  --url https://provider.example/login \
  --profile-dir ~/.uexchanges/browser/profile \
  --allowed-origin https://provider.example \
  --channel chrome \
  --out ~/.uexchanges/activation/human-login.json
```

The visible browser opens. The human performs login/SSO/2FA manually.

When authentication is complete, type exactly:

```text
DONE
```

The wrapper creates an opaque `human_login_ref` only after the human-login process exits successfully.

The evidence file stores:

- opaque `human_login_ref`;
- completion timestamp;
- SHA-256 of the dedicated profile path, not the path itself;
- browser channel;
- normalized allowed origins.

It does not store credentials, OTP, cookies or storage state.

## 5. Run value-free authenticated INSPECT

The form URL may contain provider-significant query material. That query is used only in memory when calculating the two form identities and is not exported in the INSPECT artifact.

```bash
npm run activate -- inspect \
  --url 'https://provider.example/application?call=2026' \
  --profile-dir ~/.uexchanges/browser/profile \
  --allowed-origin https://provider.example \
  --channel chrome \
  --provider generic_html \
  --runtime-token ~/.uexchanges/activation/runtime.attestation \
  --login-evidence ~/.uexchanges/activation/human-login.json \
  --out-token ~/.uexchanges/activation/inspect.attestation \
  --identity-out ~/.uexchanges/activation/inspect-identity.json
```

Current activation compiler supports `provider=generic_html` only. Provider-specific adapters must be certified in separate scoped work.

The safe identity artifact contains only:

```text
provider
page URL without query/fragment
form_fingerprint
validation_signature
browser channel
profile mode
authenticated boolean
opaque human_login_ref
inspection timestamp
safety booleans
```

No structural answer values are persisted by the activation compiler.

## 6. Create a provider manifest candidate

This creates an explicit **NON-CERTIFIED** local candidate.

```bash
npm run activate -- provider-candidate \
  --provider generic_html \
  --origin https://provider.example \
  --manifest-version candidate-v1 \
  --channel chrome \
  --playwright-version 1.62.1 \
  --requires-human-login \
  --out ~/.uexchanges/activation/provider-candidate.json
```

The command hard-codes:

```text
prefill_certified = false
submit_certified = false
```

Changing those flags is not part of target-Mac activation. Certification requires a new provider-certification lease, provider-specific adversarial QA and explicit evidence.

## 7. Pure PREFILL promotion check

The check requires a full canonical `FormExecutionPlan` JSON matching the current form identity.

```bash
npm run activate -- promotion-check \
  --plan /path/to/form-execution-plan.json \
  --manifest ~/.uexchanges/activation/provider-candidate.json \
  --runtime-token ~/.uexchanges/activation/runtime.attestation \
  --inspect-token ~/.uexchanges/activation/inspect.attestation
```

With the non-certified candidate above, the expected result is a denial containing:

```text
provider_prefill_not_certified
```

That denial is correct. Target-Mac activation proves the runtime and current form identity; it does **not** certify the provider.

Only a later committed provider manifest backed by QA evidence may make this pure check positive.

## 8. End the local session

Remove transient exported secrets from the shell when finished:

```bash
unset UEX_RUNTIME_ATTESTATION_SECRET
unset UEX_INSPECT_ATTESTATION_SECRET
```

Keep the dedicated browser profile if the authenticated session is intended to persist. Keep activation evidence private and local unless a later protocol explicitly defines a safe hash/reference projection.

## Definition of done for the human gate

The target-Mac gate is PASS only when all of these are evidenced locally:

```text
canonical doctor PASS
runtime attestation verifies
human login completes in dedicated profile
no password/OTP/cookie/storage export
authenticated INSPECT completes
form_fingerprint captured
validation_signature captured
INSPECT evidence verifies
provider manifest remains NON-CERTIFIED unless separate certification passed
no browser write executed
no Submit executed
```

After that, the next engineering step is provider-specific certification. It is not external PREFILL activation by default.
