# Form PREFILL_LOCAL Development Protocol

## Status

`PREFILL_LOCAL_ONLY` is a **development/test capability**, not an operational external-form capability.

There is intentionally no `npm run prefill` command. The implementation is currently callable only from the test harness / trusted code path and hard-rejects any canonical form URL whose hostname is not loopback:

```text
127.0.0.1
localhost
::1
```

Operational external PREFILL remains blocked until the target Mac has durable PASS evidence for:

1. target-Mac browser doctor;
2. HUMAN_LOGIN_TAKEOVER;
3. authenticated INSPECT smoke.

## Input authority

PREFILL consumes a compiled `FormExecutionPlan`. The browser does not invent ownership or answers.

The plan must be in:

```text
answer_pack_resolved
or
prefill_ready
```

It must not be expired.

Defense-in-depth validation independently rejects a forged “ready” JSON if any field still has:

```text
BLACK
UNRESOLVED
```

The only writable ownership classes are:

```text
GREEN  = verified factual prefill
YELLOW = policy-permitted assisted text requiring later human review
```

RED fields are retained as protected human fields and are never written by PREFILL.

Files/attachments are out of scope.

## Fingerprint gate

Before any DOM write:

```text
capture current DOM schema
→ compute Node fingerprint
→ compare with canonical plan form_fingerprint
```

Node fingerprint semantics have a canonical CI parity test against the Python `form_schema_fingerprint()` implementation, including Unicode, query strings, fragments and explicit ports.

Mismatch:

```text
FORM_FINGERPRINT_MISMATCH
→ zero writes
```

After prefill, schema is captured and hashed again. Any structural change during writing aborts with:

```text
FORM_STRUCTURE_CHANGED_DURING_PREFILL
```

## Browser write envelope

Supported writable native controls:

- text / textarea;
- email;
- number;
- date-like native input values;
- select;
- radio groups;
- checkbox / checkbox groups.

Not supported:

- file uploads;
- custom React/ARIA widgets;
- contenteditable;
- signatures;
- CAPTCHA;
- OTP/password fields;
- arbitrary JS execution supplied by a caller.

The browser-side write operation receives only the exact compiler-approved write set.

Output contains field keys and validation status, **not answer values**.

## Network sandbox

PREFILL is stricter than INSPECT.

Once the fixture/page is opened, every intercepted request must be:

1. same origin as the loopback form; and
2. `GET`, `HEAD` or `OPTIONS`.

Therefore these are blocked:

```text
POST autosave
PUT/PATCH/DELETE side effects
cross-origin GET exfiltration
external analytics triggered by input events
```

The live fixture deliberately tries both a same-origin POST autosave and a cross-origin GET leak after input events.

## Submit blockade

Before page scripts execute, the runtime installs:

```text
submit event preventDefault + stopImmediatePropagation
HTMLFormElement.submit → throw
HTMLFormElement.requestSubmit → throw
```

There is no click/select-upload/submit command exposed by this development slice.

`PREFILL_LOCAL_ONLY != SUBMIT_AUTHORITY`.

## Protected fields

RED/human fields are included in the plan as protected keys but omitted from the write set.

The adversarial live fixture installs an input listener on a RED field. CI requires:

```text
protectedTouchCount == 0
```

so accidentally dispatching an input/change event to a protected field fails the test.

## Secret/value leakage

Result payloads may contain:

- application ID;
- form fingerprint;
- count of written fields;
- written field keys;
- protected field keys;
- invalid field keys;
- boolean safety assertions.

They may not contain final answer values, protected values, cookies or storage state.

The live smoke serializes the result and fails if fixture email, motivation, protected declaration, URL query token or action token appear.

## CI gauntlet

The dedicated `form-executor` workflow runs a real Chromium browser and must pass:

```text
unit security guards
network-isolated doctor
live INSPECT localhost smoke
live PREFILL localhost smoke
```

The prefill fixture attacks the executor with:

- stale fingerprint test;
- scripted requestSubmit;
- same-origin POST autosave;
- cross-origin GET exfiltration;
- RED protected input listener;
- populated output leak canaries.

## Promotion gate

Moving from development-only localhost prefill to operational authenticated prefill requires a **new implementation/control-plane lease** and new tests. It must not be achieved by removing `assertLoopbackUrl()` or adding an unrestricted CLI flag.

The future production promotion must bind:

```text
target-runtime PASS
canonical Application ID
current form fingerprint
compiled plan hash
allowed origin/provider adapter
capability mode = PREFILL_ONLY
```

and it still may not submit.
