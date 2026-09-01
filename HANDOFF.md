# UE-Xchanges-OS — HANDOFF

Checkpoint: 2026-09-02 00:22 Europe/Madrid

Purpose: allow a zero-context agent to recover current execution without relying on chat memory.

## Cold start — mandatory order

1. Read `goal.md`.
2. Read active `LIVE-STATE-OVERRIDE.json` for current aggregate domain state.
3. Read `STATE.md`.
4. Read `AGENTS.md` and `docs/MULTI_AGENT_CONTROL_PLANE.md`.
5. Read `docs/RUNTIMEGRAPH_V1.md` and `RUNBOOKS/RUNTIMEGRAPH_RECOVERY.md`.
6. Read the newest checkpoint in `checkpoints/`.
7. Read private Drive CRM Dashboard, `Agent_Sessions`, `Work_Leases`, and the tail of `Agent_Event_Bus`.
8. Load/recompile RuntimeGraph from the current `Mass_Apply_Queue`; never assume the stored snapshot is fresh after material domain changes.
9. Search Gmail for organiser replies newer than the checkpoint and read full threads.
10. Before canonical mutation, acquire a fresh narrow lease; before runtime-action mutation, acquire the exact action lease.
11. Persist evidence/gate changes in Drive first, then recompute RuntimeGraph and downstream projections.

## Canonical resources

- Drive CRM: `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`
- Drive handoff folder: `1T8EW70y2Clfhnug3vRqRhtTtqDqvQPid`
- RuntimeGraph read model: `16QcHOWoBD1ixstPkhivftuyqmQdhtZj6`
- RuntimeGraph machine snapshot: `1iVyNAZWmURTdK8wZyYjYxyYDh9Djik3P`
- Private recovery pack: `19tM23N37cqweaWPSoVMxEECZhfOSrEJPGj_nRJB71q4`
- Todoist project: `6hCjVwH7R6hq49G3`
- Todoist W9 control: `6hPPRQrhG6cmhh3V`
- GitHub repo: `rotprods/UE-Xchanges-OS`

## Aggregate state after latest P1 discovery

- Canonical opportunities: **176**.
- Mass Apply / application nodes: **164**.
- Organisations: **30**.
- Current-wave receipt-backed submissions: **0**.

The new canonical opportunity is `non_salto-convivial-foodscapes-2026` (`CONVIVIAL FOODSCAPES`), P1, deadline `2026-09-15`, state `POLICY_GATE_PENDING`. It remains intentionally outside `Mass_Apply_Queue` while `AI_POLICY_UNKNOWN` and `FULL_NOVEMBER_AVAILABILITY_UNCONFIRMED` remain unresolved. Read `checkpoints/2026-09-02-convivial-foodscapes-p1-handoff.md` before touching it.

## RuntimeGraph state

Compiler baseline `80d31479d2bb8572623d9b4a385e457d49761c11` compiled 164 Mass Apply rows into:

- 177 atomic actions;
- 656 gates;
- 1,211 edges;
- Human READY 1;
- Agent READY 145;
- System READY 10;
- Waiting 8.

This is a **derived projection**. Recompile after any material opportunity/application/gate update that changes executable application state. The CONVIVIAL discovery alone does not justify forcing a Mass Apply node while its hard gates are unresolved.

At materialisation the one application Human READY action is COMPASS payment/receipt/Tally. Todoist task `6hQ5Xhgp8hPVgc7V` carries the RuntimeGraph pointer. Do not infer that older Todoist `human_now` tasks remain READY; the runtime graph must decide application readiness from current evidence/deadline gates.

## Runtime action protocol

```text
READ GRAPH
→ choose highest-priority READY action
→ verify executor ownership
→ acquire exact runtime_action lease
→ execute bounded action
→ verify expected output/evidence
→ emit idempotent event
→ persist canonical evidence if domain truth changed
→ recompute graph/frontiers
→ release lease
```

Human-only: authentication/MFA/CAPTCHA, identity/sensitive values, payment, applicant-owned final wording where required, personal video, irreversible submit.

Agent: reversible source/form/infopack verification, evidence mapping, factual prefill where policy allows, QA, receipt verification, gate recomputation, projection/recovery.

## Form boundary

Read `docs/RUNTIMEGRAPH_FORM_GATEWAY.md` before operating a captured application form.

- RuntimeGraph selects the next action.
- Form Execution Gateway represents typed fields/ownership/auth/attempts/receipts.
- `SubmissionAttempt != SubmissionReceipt`.
- Final irreversible submit is HUMAN in RuntimeGraph v1.
- Never expose BLACK/secret form-field values to public state or model-visible projections.

## Hard evidence rules

- `ROUTE_QUERY_SENT != APPLICATION_SUBMITTED`
- `ELIGIBLE != SELECTED`
- `INVITED_TO_APPLY != ACCEPTED`
- `PAYMENT_REQUIRED_FOR_PLACE != CONFIRMED`
- expired deadline requires extension/late/open evidence before irreversible action;
- no `APPLICATION_SUBMITTED` without receipt or authoritative confirmation;
- latest authoritative organiser/source evidence overrides older summaries;
- Todoist/Notion/HubSpot/RuntimeGraph are projections, not receipt authority.

## New P1 — CONVIVIAL FOODSCAPES

- ID: `non_salto-convivial-foodscapes-2026`
- Role: visual artist.
- Host/location: Quinta das Relvas x CONVIVIUM, Branca, Portugal.
- Residency: `2026-11-01` → `2026-11-30`.
- Deadline: `2026-09-15`.
- Spain gate: PASS.
- Funding captured from official call: flights + accommodation; meals excluded; €1,000 financial support; up to €150 materials/small-tools reimbursement; possible later exhibition transport/insurance support up to €1,250 if selected.
- Strong media/creative fit: visual, digital, conceptual, performative and research-based work; analogue photo lab subject to availability, DSLR, studio lighting and multimedia equipment.
- Application package: portfolio max 5 pages, website/social, CV, one-page motivation.
- Hard gates: `AI_POLICY_UNKNOWN`; `FULL_NOVEMBER_AVAILABILITY_UNCONFIRMED`.
- Required next gate: `VERIFY_AI_POLICY_AND_NOVEMBER_AVAILABILITY_THEN_PREPARE`.
- Do not recommend submit and do not enqueue into Mass Apply before both hard gates pass.
- Official source: `https://quintadasrelvas.pt/convivialfoodscapes/`.

## Next safe frontier

1. Read `Agent_Frontier`; execute reversible verification actions in priority/deadline order under leases.
2. Persist resulting source/gate changes to Drive.
3. Recompile RuntimeGraph after executable-state changes.
4. Present only newly READY `Human_Frontier` actions to Roberto.
5. After human execution, verify receipts and advance application/outcome state.
6. Continue W9 until receipt/cohort stop contract passes.
7. For CONVIVIAL specifically, resolve AI-policy evidence and full-November availability before any application preparation/queue promotion.
8. Continue SALTO paid trainer watch; the announced September 2-plenary + 5-co-creation-lab facilitator wave is not an open call until actual call/fee/eligibility evidence exists.

Current application Human Frontier begins with COMPASS. The large Agent Frontier intentionally contains old-deadline verification/archival actions because RuntimeGraph no longer trusts historical T0/T1 labels after the calendar deadline.

## Tool ownership

- Gmail / official portal: external evidence.
- Drive CRM + Event Bus: canonical operational truth and provenance.
- GitHub: code/contracts/schemas/public recovery state.
- RuntimeGraph: derived execution frontier.
- Todoist: human/control projection only.
- Notion: reconstructible cockpit only.
- HubSpot: relationship graph only.

## Whole-project state

RuntimeGraph implementation does not complete W9. Current-wave receipts remain 0; P0 human conversion and large Agent Frontier remain active. Canonical Drive now has 176 opportunities while the last Notion projection snapshot was 175; treat that as projection lag, not domain ambiguity. Do not return to architectural expansion unless execution reveals a repeatable failure requiring a new invariant/test.
