# Form Plan Identity v2

## Purpose

Plan Identity v2 makes one submission identity depend on three independent facts:

```text
form structure
+ native validation rules
+ canonical semantic answer payload
```

A browser-visible form can therefore invalidate an earlier approval even when question labels and answers look unchanged.

## Identity chain

```text
form_fingerprint
+ validation_signature
+ answer_pack_hash(canonical answers)
→ submission_key

complete plan metadata
+ validation_signature
+ canonical answers
→ execution_plan_hash

application_id
+ form_fingerprint
+ validation_signature
+ submission_key
+ execution_plan_hash
→ HMAC ApprovalToken
```

`validation_signature=None` remains allowed for discovery/research/capture compatibility. It is represented as an explicit `validation:unbound` identity in the submission key so it cannot collide with a validation-bound plan.

A plan without a validation signature **cannot receive an ApprovalToken**.

## Canonical answer normalization

Normalization is used for hashing/comparison identity only. It does not rewrite the text shown to the human or silently alter browser payloads.

Rules:

- text/textarea: Unicode NFC; CRLF/CR → LF; meaningful outer whitespace preserved;
- email: Unicode NFC + line-ending normalization + outer trim; local/domain case is not rewritten;
- number: finite decimal identity; `1`, `1.0`, `1.00` → `1`; negative zero → `0`;
- date: `date` or strict ISO `YYYY-MM-DD` → ISO calendar date;
- select/radio: Unicode NFC + outer trim;
- checkbox: boolean for a single checkbox, otherwise sorted unique normalized option strings;
- consent: boolean only;
- file/unknown: non-null model-visible values rejected from canonical answer identity;
- BLACK: no model-visible answer may enter normalization.

## Security properties

### Representation noise does not create duplicate identities

Equivalent numeric, Unicode, checkbox-order and line-ending representations hash identically.

### Material validation changes invalidate approval

Changing native validation rules produces a new `validation_signature`, which changes `submission_key`, `execution_plan_hash`, and the ApprovalToken binding.

### Old approval tokens fail closed

Approval claims now require `validation_signature`. Tokens issued under the older claim set parse as malformed rather than being silently upgraded.

### Research compatibility does not imply submit compatibility

An unbound plan may still exist and may be useful for form capture, evidence mapping or local development. Approval issuance rejects it.

## Remaining capability gate

This release changes identity/security contracts only. It does **not** enable:

- external PREFILL;
- browser Submit;
- file upload;
- payment;
- secret/cookie/storage export.

Operational browser promotion remains blocked by the target-Mac doctor, human login and authenticated-inspect evidence gate.
