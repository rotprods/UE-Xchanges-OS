# Form Browser Executor — Restricted Capability Ladder

## Status

Implemented capabilities:

```text
INSPECT_ONLY
HUMAN_LOGIN_TAKEOVER
```

Not implemented/authorised yet:

```text
PREFILL_ONLY
VALIDATE_AND_DIFF
SUPERVISED_SUBMIT
AUTONOMOUS_SUBMIT
```

A capability existing in the codebase does not grant the next capability. Each stage receives a separate control-plane lease, tests and release evidence.

The production architecture intentionally does **not** expose raw Playwright MCP tools to the autonomous application agent. A raw browser-control surface could bypass UE-Xchanges hard gates. Instead, the restricted executor uses the Playwright library behind purpose-built commands.

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

The dependency is pinned exactly in `package.json`. A generated lockfile should be committed from the target Mac runtime once dependency installation is performed there and verified; the repository must not pretend an ungenerated lock exists.

## Runtime verification gate

Before using the browser executor on a real opportunity, the target machine must pass:

```bash
npm run doctor -- --channel chrome
```

The doctor:

- uses an ephemeral temporary profile, never the persistent authenticated UEX profile;
- runs headless only for launch verification;
- blocks all network requests;
- visits only `about:blank`;
- returns the Node major, pinned Playwright version, selected browser channel and launch status;
- deletes the temporary profile;
- never reads cookies, browser storage or page data.

Expected shape:

```json
{
  "status": "ok",
  "node_major": 22,
  "playwright_version": "1.62.1",
  "browser_channel": "chrome",
  "launch": "ok",
  "network": "blocked",
  "profile": "ephemeral"
}
```

GitHub also runs a dedicated `form-executor` workflow. It installs the pinned package and Playwright Chromium runtime, runs the unit security guards, runs the network-isolated doctor, then launches a **real Chromium browser** against a form served only on `127.0.0.1`.

The live fixture deliberately contains query tokens, populated private values, a password, an OTP, an attempted POST telemetry call and a scripted `requestSubmit()`. CI must prove that:

- structural fields are extracted correctly;
- query/field/password/OTP values are not exported;
- no mutating request reaches the fixture server;
- scripted submission remains blocked;
- form action/query output is redacted.

That CI workflow has `contents: read`, uses no repository secrets and never contacts a real application form.

# INSPECT_ONLY

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
- output URLs strip query, fragment and userinfo material;
- raw Playwright errors are not emitted;
- no cookies are read;
- no Playwright storage state is exported;
- no local/session storage is read;
- no click/fill/check/select/upload/keyboard-write Playwright APIs exist in this module.

This conservative network policy may prevent some modern SPAs from loading if they use POST requests for read-only GraphQL queries. That is an explicit safety trade-off. Provider-specific read-only exceptions require a reviewed adapter; they must not be silently relaxed globally.

## Inspector output

The inspector returns JSON containing:

```text
redacted page URL/title/origin
native forms + redacted method/action
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

# HUMAN_LOGIN_TAKEOVER

This mode exists solely to establish legitimate authentication inside the dedicated UEX browser profile **without giving the agent credential access**.

Example:

```bash
npm run human-login -- \
  --url 'https://accounts.example.org/' \
  --allowed-origin 'https://accounts.example.org' \
  --allowed-origin 'https://application.example.org'
```

The initial `--url` must be a provider/base login URL with no query string, fragment or embedded username/password. This avoids leaking tokenised URLs through command-line process metadata.

If SSO redirects across providers, every legitimate top-level origin must be listed explicitly with another `--allowed-origin`. Subresources may load normally.

## Login takeover sequence

```text
program opens dedicated persistent profile
→ initial allowlisted GET navigation
→ program stops interacting with the page
→ human uses visible browser manually
→ human enters username/password/SSO/2FA/CAPTCHA as required
→ human returns to terminal
→ human types DONE
→ browser context closes
→ browser profile retains its legitimate session locally
```

The login program requires an interactive TTY. It does not support headless mode or an automation acknowledgement flag.

## What HUMAN_LOGIN_TAKEOVER may do

- launch the dedicated persistent browser profile;
- navigate once to the provided base login URL;
- allow browser network traffic required by the human login flow;
- enforce the explicit allowlist for top-level navigation;
- wait for the human to type `DONE`;
- close the context cleanly so the local profile persists its normal browser session.

## What it may not do

The login implementation contains no API for:

- DOM evaluation or locators;
- reading text/attributes/input values;
- agent-driven click/fill/check/select;
- keyboard automation;
- file upload;
- cookie extraction;
- `storageState` export;
- localStorage/sessionStorage reads;
- raw Playwright errors or page-content logging;
- form/application submission on the user's behalf.

The browser itself necessarily receives credentials/cookies during a legitimate login, but those values remain inside the browser/profile boundary and are never exported to the model or project stores.

## Important distinction

```text
AUTHENTICATED_PROFILE != APPLICATION_SUBMIT_AUTHORITY
```

A successful login only enables a later capability to open an authenticated page. It does not satisfy eligibility, AI policy, human review or approval-token gates and does not create a `SUBMITTED` state.

# Unsupported forms

The generic inspector currently handles native:

- input
- textarea
- select
- radio groups
- checkbox groups
- file inputs structurally

Custom React/ARIA/contenteditable controls are counted as unsupported custom controls rather than guessed. Provider adapters will be added only after the generic boundaries prove safe.

# Required progression

```text
INSPECT_ONLY
→ browser CI live local-form smoke GREEN
→ target-Mac doctor GREEN
→ HUMAN_LOGIN_TAKEOVER
→ authenticated inspect smoke
→ PREFILL_ONLY
→ deterministic validation + form diff
→ human approval capability
→ supervised submit
→ receipt verification
```

The approval capability already exists in the canonical Python core, but the browser is not yet connected to it. No current mode implies permission for the next mode.
