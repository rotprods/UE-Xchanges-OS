# Form Runtime Attestation & PREFILL Promotion Gate

## Status

This layer is a **pure security/control-plane gate**. It does not add browser interaction, external PREFILL, Submit, upload, payment or secret export.

The goal is to prevent a future external browser actuator from gaining authority merely because:

- Playwright is installed;
- a browser profile exists;
- a login happened once;
- a form was inspected at some earlier point; or
- a provider name appears in a configuration file.

PREFILL promotion requires all of those facts to be current, signed and mutually consistent.

## Runtime doctor evidence

The canonical doctor output is modeled as `RuntimeDoctorEvidence` and is valid only when:

```text
status = ok
Node major >= 20
browser channel = chrome | chromium | msedge
launch = ok
network = blocked
profile = ephemeral
Playwright version is non-empty
```

The evidence is deterministically hashed. `issue_runtime_attestation()` accepts the structured doctor evidence, not an arbitrary caller-supplied hash.

The doctor evidence is intentionally ephemeral. The resulting runtime attestation describes the real execution profile separately as:

```text
profile_mode = dedicated_persistent
```

## Runtime attestation

Runtime attestation is a domain-separated HMAC capability:

```text
uexrt1.<payload>.<signature>
```

It binds:

- opaque runtime reference;
- executor version;
- Playwright version;
- browser channel;
- dedicated profile mode;
- deterministic doctor evidence hash;
- doctor time;
- issue/expiry time;
- nonce.

Maximum TTL: 24 hours.

`runtime_ref` must be an opaque application-level reference. It must not contain a hardware serial, password, cookie, OTP or other secret.

The signing secret is a local runtime secret. It must stay in a local secret store/environment and must never be pasted into ChatGPT, committed to GitHub or written to Drive.

## Authenticated INSPECT evidence

A second domain-separated token:

```text
uexinsp1.<payload>.<signature>
```

binds one inspection to:

- runtime attestation ID;
- provider ID;
- canonical form URL;
- `form_fingerprint`;
- `validation_signature`;
- authenticated/not-authenticated state;
- opaque human-login reference when authenticated;
- inspection/expiry time;
- mandatory safety claims:
  - `form_values_read = false`
  - `cookies_read = false`
  - `storage_state_exported = false`.

Maximum TTL: 1 hour, further capped by the runtime attestation expiry.

If `authenticated=true`, a non-empty `human_login_ref` is mandatory. That reference is not a password/OTP/cookie and does not prove identity by itself; it is an opaque durable reference to the locally completed human-login takeover event.

## Provider capability manifests

Provider permissions are explicit data, not inferred from a URL.

A manifest controls:

- provider ID and manifest version;
- allowed origins;
- whether INSPECT is supported;
- whether human login is supported/required;
- whether PREFILL is certified;
- whether Submit is certified;
- certified executor versions;
- certified Playwright versions;
- certified browser channels;
- QA evidence references;
- whether the manifest is loopback-only.

The loader rejects unknown keys and malformed/duplicate capability data.

### Current repository state

Only one manifest is present:

```text
config/form-providers/generic-html-local-fixture.json
```

It is:

```text
PREFILL certified: yes
scope: localhost / 127.0.0.1 only
browser: chromium
Submit certified: no
```

Repository tests require that every committed `prefill_certified=true` manifest remains `local_fixture_only=true` and that no committed manifest has `submit_certified=true`.

Therefore **zero external providers are certified for PREFILL and zero providers are certified for Submit** at this stage.

## PREFILL promotion decision

`evaluate_prefill_promotion()` is pure. It does not open a browser or issue a browser command.

A positive decision requires:

```text
plan is PREFILL-ready
plan has validation_signature
runtime attestation signature + TTL valid
inspect evidence signature + TTL valid
provider manifest matches plan.provider
plan origin is manifest-certified
executor version certified
Playwright version certified
browser channel certified
inspect runtime_attestation_id == current runtime attestation
inspect provider == plan provider
inspect canonical URL == plan canonical URL
inspect form_fingerprint == plan form_fingerprint
inspect validation_signature == plan validation_signature
human login evidence present when provider requires login
manifest.prefill_certified == true
```

Any failure returns a deterministic denial reason such as:

```text
runtime_attestation_invalid
inspect_evidence_invalid
plan_not_prefill_ready
plan_validation_unbound
provider_manifest_mismatch
provider_prefill_not_certified
provider_origin_not_certified
executor_version_not_certified
playwright_version_not_certified
browser_channel_not_certified
inspect_runtime_binding_mismatch
inspect_form_fingerprint_mismatch
inspect_validation_signature_mismatch
human_login_evidence_required
```

A successful decision returns only a `capability_binding_hash` plus opaque attestation/evidence IDs. It does **not** issue or execute a browser write capability yet.

## Why this blocks stale authentication

A persistent Chrome profile can survive for days. That does not make its state current enough for autonomous operation.

The runtime gate instead requires short-lived signed evidence tied to the current:

```text
runtime
+ provider
+ canonical URL
+ form structure
+ validation rules
+ plan identity
```

If the form changes, the validation signature changes, the browser runtime changes version/channel, the inspection expires, or the provider manifest does not explicitly certify PREFILL, promotion fails closed.

## Target-Mac activation

The existing human task remains mandatory before any external promotion work:

```text
HUMAN NOW — UEX Form Executor: Mac doctor + persistent login smoke
Todoist: 6hQ6fqFw57wQrR6V
```

The future Mac integration should:

1. run `npm run doctor -- --channel chrome`;
2. parse that exact JSON into `RuntimeDoctorEvidence`;
3. sign a runtime attestation locally;
4. run HUMAN_LOGIN_TAKEOVER where required;
5. perform authenticated INSPECT without exporting field values/cookies/storage state;
6. sign the inspect evidence locally;
7. evaluate a provider manifest + current Plan Identity v2;
8. only then consider issuing a separate PREFILL capability token.

That final operational capability does not exist in this release.

## Submit remains a separate future authority

Nothing in runtime attestation implies Submit authority.

```text
RUNTIME_VALID != PREFILL_CERTIFIED
PREFILL_CERTIFIED != SUBMIT_CERTIFIED
AUTHENTICATED != HUMAN_APPROVED
CLICK_SUBMIT != SUBMITTED_CONFIRMED
```

A future Submit actuator must still satisfy ApprovalToken, idempotency, attempt-before-click and receipt reconciliation contracts already present in the Form Execution Gateway.
