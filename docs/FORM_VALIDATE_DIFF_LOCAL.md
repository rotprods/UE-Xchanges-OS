# Form VALIDATE_AND_DIFF Local Protocol

## Status

`VALIDATE_AND_DIFF_LOCAL_ONLY` is a development/test capability. It does not activate external PREFILL or SUBMIT.

The purpose is to answer, without exporting form values:

```text
Is this still the same form?
Did native validation rules change?
Do current field values equal the approved/compiled plan?
Are current fields natively valid?
Which field keys changed or mismatch?
```

## Two freshness identities

The gateway now treats these as separate contracts:

### Structural form fingerprint

Existing fingerprint covers:

```text
provider
canonical URL
field key
label
type
required
options
maxlength
```

### Native validation signature

The validation sidecar additionally covers:

```text
minlength
maxlength
pattern
min
max
step
multiple
accept
```

This split is intentional. A form can keep the same questions while materially changing what inputs are accepted.

External PREFILL/approval/submit promotion MUST eventually bind both:

```text
form_fingerprint
validation_signature
```

Until that binding is integrated into the operational execution-plan/approval capability, external PREFILL remains blocked by policy even if localhost tests are green.

## Canonical parity

`src/uexchanges/forms/validation_rules.py` owns the Python validation signature contract.

`tools/form-executor/src/validation-signature.mjs` implements the browser-runtime equivalent.

CI requires exact Python↔Node parity over:

- Unicode labels/options;
- query + fragment URL handling;
- explicit ports;
- minlength/maxlength;
- pattern;
- min/max/step;
- multiple;
- file accept lists.

## Validation expectation

A `ValidationExpectation` contains:

```text
provider
canonical_form_url
validation field snapshot
signature
```

Construction rejects duplicate field keys and a signature that does not match its own snapshot.

This is a sidecar contract for the current development phase. It is not submission evidence.

## Diff report

Schema diff output contains only:

```text
added_field_keys
removed_field_keys
changed_fields:
  field_key
  changed_properties[]
```

For example:

```json
{
  "field_key": "motivation",
  "changed_properties": ["constraints.minlength"]
}
```

It intentionally does **not** include old/new constraint values or any field answers.

## Current-value validation

The trusted browser runtime may compare current DOM values with the compiled plan internally.

Output per field is limited to:

```text
field_key
present
value_match
valid
ownership
editable_by_agent
```

No current value or expected answer is returned.

RED fields may be compared to a human-owned plan value because RED is private/human-confirmed, not BLACK/SECRET. BLACK fields are impossible in a prefill-ready plan and remain outside this capability.

## Browser boundary

The local live test runs Chromium only against `127.0.0.1`.

It proves:

1. exact expected state -> fingerprint/signature/value/validity PASS;
2. a changed current value -> only its field key reports mismatch;
3. a changed native rule -> validation signature fails and diff reports only the changed property name;
4. report serialization contains none of the answer/query canaries.

No external site, authenticated user profile or application submit is used.

## Known normalization boundary

Browser-native text-like values are strings. Operational promotion must define canonical value normalization for numeric/date/boolean fields before external use. Current localhost validation tests deliberately exercise string/select fields and checkbox/radio handling remains covered by PREFILL tests.

This is a **known blocked integration item**, not permission to treat cross-type comparisons as authoritative yet.

## Required next integration

Before external PREFILL can be activated:

1. target-Mac doctor PASS;
2. HUMAN_LOGIN_TAKEOVER PASS;
3. authenticated INSPECT PASS;
4. validation signature captured from the authoritative form version;
5. `FormExecutionPlan`/approval binding extended to validation signature;
6. canonical value-normalization rules completed and tested;
7. authenticated PREFILL dry run with no Submit;
8. human review UI/diff surface.

Only after all of those may a later supervised-submit slice be considered.

## Non-goals

This capability does not:

- fill an external form;
- click Submit;
- upload files;
- handle passwords/OTP/CAPTCHA;
- read/export cookies or storage state;
- create an approval token;
- create a SubmissionAttempt;
- create a receipt;
- mark an application SUBMITTED.
