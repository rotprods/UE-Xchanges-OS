# RuntimeGraph V2.4 — Provider / Form Capture Executor

## Objective

Promote one narrowly bounded capability: **external provider INSPECT** for explicitly certified public form providers.

The capability exists to resolve `WAITING_VALUE_SAFE_FORM_SCHEMA_CAPTURE` without granting external PREFILL, authentication or Submit.

## Execution path

```text
RuntimeGraph Agent action
→ browser_capture_provider_form
→ repository provider manifest
→ loopback MCP Relay
→ loopback Browser Worker
→ ephemeral Chromium context
→ certified HTTPS origins only
→ GET / HEAD / OPTIONS only
→ provider-specific value-free extractor
→ question schema + fingerprint + safety evidence
→ NormalizedIngress / affected application subgraph
```

## Capability boundary

Allowed:

- open an explicitly certified public form URL;
- follow redirects only across origins listed in the provider manifest;
- load only GET/HEAD/OPTIONS requests from certified origins;
- extract question labels, field type, required flag, choices and maxlength where visible;
- calculate form fingerprint;
- bind the capture to an exact `application_id`;
- close the ephemeral browser context after capture.

Forbidden:

- reading or exporting current answer values;
- reusing applicant browser cookies/session state;
- login, SSO, MFA, CAPTCHA or identity fields;
- POST/PUT/PATCH/DELETE requests;
- external PREFILL;
- file upload;
- payment;
- Submit;
- receipt inference.

## First certified provider

`google_forms` is the only RG2.4 external provider manifest.

Manifest:

`config/form-providers/google-forms-inspect-v1.json`

The manifest certifies **INSPECT only**. `prefill_certified=false` and `submit_certified=false` are hard requirements for the capture registry.

## Google Forms extractor

Google Forms uses custom ARIA controls rather than relying exclusively on native HTML form controls. RG2.4 therefore adds a provider-specific extractor that maps visible question containers into the canonical value-free field model.

The extractor emits:

```text
field_key
label
field_type
required
options
maxlength
ownership=unresolved
sensitivity=private
editable_by_agent=false
```

It never exports the current value of a field.

## Network safety

The external provider-capture browser is a new ephemeral context, separate from the persistent authenticated browser profile.

Every request is rejected unless:

1. the method is GET, HEAD or OPTIONS; and
2. the URL origin exists in the repository provider manifest; and
3. the external URL uses HTTPS.

The page receives an init script that blocks `submit`, `requestSubmit` and submit events before site code runs.

## RuntimeGraph transitions

Success:

```text
WAITING_VALUE_SAFE_FORM_SCHEMA_CAPTURE
→ PROVIDER_FORM_CAPTURED
→ exact question-schema evidence
→ downstream form/policy/evidence actions may recompute
```

Failure remains explicit:

```text
PROVIDER_NOT_CERTIFIED
PROVIDER_TARGET_ORIGIN_NOT_CERTIFIED
PROVIDER_CAPTURE_SCHEMA_EMPTY
PROVIDER_CAPTURE_FINAL_ORIGIN_NOT_CERTIFIED
WAITING_EXTERNAL_ROUTE_ARTIFACT
```

No failure promotes a human or submission state by itself.

## Tests

RG2.4 adds:

- deterministic Google Forms question normalization tests;
- HTTPS/origin/mutating-method policy tests;
- provider-registry fail-closed tests;
- MCP surface test proving the new capture tool exists while Submit/cookie/storage/upload/payment tools remain absent;
- a dedicated GitHub Actions live smoke against the public Game of Nature Google Form.

The live smoke asserts a non-empty question schema plus `form_values_read=false`, `answer_values_exported=false`, `external_prefill_available=false`, and `submit_available=false`.

## Stop condition

RG2.4 is accepted only when:

1. exact-head normal CI passes;
2. exact-head `provider-capture` CI passes including the live external smoke;
3. PR merges cleanly;
4. post-merge main CI passes;
5. the resulting capture is ingested into RuntimeGraph without any payment/auth/PREFILL/Submit mutation.
