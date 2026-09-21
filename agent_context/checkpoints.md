# UE-Xchanges-OS — Checkpoint Index

> Derived navigation only. Current GitHub main, private Drive/EventBus and fresh provider evidence override every snapshot here.

## Current seal

- Timestamp: `2026-09-21T21:59:00+02:00`
- Baseline main: `c0c31fed602a1ad774a7c6416a4abd7e09d26dde`
- Checkpoint: [`../checkpoints/2026-09-21-portfolio-convergence-seal.md`](../checkpoints/2026-09-21-portfolio-convergence-seal.md)
- Master plan: [`../plans/2026-09-21-portfolio-convergence-master.md`](../plans/2026-09-21-portfolio-convergence-master.md)
- Continuation: [`NEXT_DEATHSAFE.md`](NEXT_DEATHSAFE.md)

## Material state represented

- live P0 provider changes reconciled into private canonical Applications;
- global barriers enforced by bootstrap/WriterAuthorization 1.3;
- private Elba/STORY form packets exist;
- RuntimeGraph remains stale and awaits full rebuild;
- external/human gates, not historical scheduler milestones, define the current frontier.

## Create a new checkpoint when

- a P0 application reaches receipt-backed submission/selection/terminal state;
- RuntimeGraph full rebuild reaches a current watermark;
- cold-start/global-barrier semantics change;
- a material PR convergence changes outbound safety;
- a new provider message materially changes deadline/route/eligibility.

## Historical pointers

Older Sep1/Sep2/Sep10/Sep15/Sep18 checkpoints remain historical evidence only. They must not override this index or live authority.
