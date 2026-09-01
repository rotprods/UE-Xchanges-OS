# Form Browser Executor — Inspect-Only Bootstrap

## Status

Current mode: `INSPECT_ONLY`.

This component may open a form and extract its **structure**. It cannot fill fields, click controls, upload files, export cookies/session state, or submit anything.

The production architecture intentionally does **not** expose raw Playwright MCP tools to the autonomous application agent. A raw browser-control surface could bypass UE-Xchanges hard gates. Instead, the restricted executor uses the Playwright library behind a purpose-built command surface.

Current pinned browser library: `playwright@1.62.1`.

## Runtime requirements

- Node.js 20+
- Chrome, Chromium or Microsoft Edge depending on selected channel
- a dedicated UEX browser profile

Default profile:

```text
~/.uexchanges/browser/profile
```

The executor explicitly refuses common normal Chrome/Chromium/Edge profile roots. Do not point it at your everyday browser profile.

## Install

From the repository:

```bash
cd tools/form-executor
npm install
```

The dependency is pinned exactly in `package.json`. A generated lockfile should be committed from the target Mac runtime once dependency installation is performed there and verified; this bootstrap PR does not pretend that an ungenerated lock exists.

## Public-form inspection

```bash
npm run inspect -- \
  --url 'https://example.org/application' \
  --allowed-origin 'https://example.org'
```

Optional:

```text
--profile-dir PATH
--allowed-origin ORIGIN     repeatable for legitimate redirects
--channel chrome|chromium|msedge
--timeout-ms 20000
--headless
```

Unknown arguments are rejected. There is deliberately no `--fill`, `--click`, `--submit`, `--upload`, `--cookie` or arbitrary-JavaScript flag.

## Inspect-only safety envelope

During an inspection session:

- only `GET`, `HEAD` and `OPTIONS` network methods are allowed;
- `POST`, `PUT`, `PATCH`, `DELETE` and other methods are aborted;
- top-level navigations outside the explicit origin allowlist are aborted;
- DOM submit events are prevented;
- direct `HTMLFormElement.submit()` and `requestSubmit()` are replaced with blocking functions;
- no current form field values are extracted;
- no cookies are read;
- no Playwright storage state is exported;
- no local/session storage is read;
- no click/fill/check/select/upload/keyboard-write Playwright APIs exist in this module.

This conservative network policy may prevent some modern SPAs from loading if they use POST requests for read-only GraphQL queries. That is an explicit safety trade-off. Provider-specific read-only exceptions require a future reviewed adapter; they must not be silently relaxed globally.

## Output

The inspector returns JSON containing:

```text
page URL/title/origin
native forms + method/action
captured native fields
required flags
select/radio/checkbox options
maxlength
submit-control metadata
count of unsupported custom controls
allowed origins
safety assertions
```

It does **not** return input values.

Password inputs and fields with `autocomplete=one-time-code` are represented structurally as `BLACK/SECRET`, with no value.

All other fields enter as `UNRESOLVED/PRIVATE`. The canonical Python compiler subsequently decides GREEN/YELLOW/RED ownership and AI policy using UE-Xchanges evidence. The browser is not allowed to make those decisions.

## Persistent authentication

The executor uses Playwright `launchPersistentContext` so the dedicated UEX profile can eventually preserve legitimate login state without copying cookies into the model.

However, **this INSPECT_ONLY mode cannot perform login**, because login normally requires POST requests. An authenticated profile must already exist to inspect a private page.

A later `HUMAN_LOGIN_TAKEOVER` mode will be implemented as a separate capability/lease. It will let Roberto perform login/2FA manually inside the dedicated profile while the agent remains unable to see credentials. That mode is not present yet.

## Unsupported forms

The generic inspector handles native:

- input
- textarea
- select
- radio groups
- checkbox groups
- file inputs structurally

Custom React/ARIA/contenteditable controls are counted as unsupported custom controls rather than guessed. Provider adapters will be added after this generic boundary proves safe.

## Required progression

The capability sequence remains:

```text
INSPECT_ONLY
→ inspected fixtures/public forms
→ HUMAN_LOGIN_TAKEOVER
→ PREFILL_ONLY
→ deterministic validation + diff
→ human approval capability
→ supervised submit
→ receipt verification
```

Each transition requires a new control-plane lease and its own tests. No current mode implies permission for the next mode.
