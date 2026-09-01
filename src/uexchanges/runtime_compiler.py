from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .models import GateResult
from .runtime_graph import ActionNode, ActionState, ExecutorType, GateNode, RuntimeGraph


@dataclass(frozen=True)
class AtomicStep:
    action_type: str
    executor: ExecutorType
    instruction: str


def compile_mass_apply_row_atomic(
    row: Mapping[str, Any], *, now: datetime | None = None
) -> RuntimeGraph:
    now = now or datetime.now(timezone.utc)
    _aware(now, "now")
    application_id = _required(row, "Application ID")
    opportunity_id = _required(row, "Opportunity ID")
    deadline = _parse_deadline(row.get("Deadline"))
    submit_state = str(row.get("Submit State") or "")
    next_action = str(row.get("Next Action") or "VERIFY_CURRENT_STATE")

    graph = RuntimeGraph()
    deadline_result, deadline_reason = _deadline_gate(row, deadline=deadline, now=now)
    gate_specs = (
        ("spain", "Spain Gate", parse_live_gate_result(str(row.get("Spain Gate") or ""), kind="spain"), str(row.get("Spain Gate") or "")),
        ("role", "Role Gate", parse_live_gate_result(str(row.get("Role Gate") or ""), kind="role"), str(row.get("Role Gate") or "")),
        ("form_ai", "Infopack/Form/AI", parse_live_gate_result(str(row.get("Infopack/Form/AI") or ""), kind="form"), str(row.get("Infopack/Form/AI") or "")),
        ("deadline", "Deadline Gate", deadline_result, deadline_reason),
    )
    gate_ids: list[str] = []
    for suffix, name, result, reason in gate_specs:
        gate_id = f"gate:{application_id}:{suffix}"
        gate_ids.append(gate_id)
        graph.add_gate(
            GateNode(
                gate_id=gate_id,
                application_id=application_id,
                name=name,
                result=result,
                reason=reason,
            )
        )

    if _terminal_submit_state(submit_state):
        steps = [AtomicStep("TERMINAL_ARCHIVE", ExecutorType.SYSTEM, "Preserve terminal evidence; do not submit.")]
    elif deadline_result is GateResult.FAIL:
        steps = [_agent("VERIFY_DEADLINE_EXTENSION_OR_ARCHIVE")]
    elif deadline_result is GateResult.UNKNOWN and _is_irreversible(next_action):
        steps = [_agent("VERIFY_EXACT_DEADLINE_OR_LATE_ROUTE"), *decompose_next_action(next_action)]
    else:
        steps = decompose_next_action(next_action)

    action_ids = [f"action:{application_id}:{index:02d}" for index in range(1, len(steps) + 1)]
    previous_id: str | None = None
    for index, (step, action_id) in enumerate(zip(steps, action_ids), start=1):
        requirements = list(_gate_requirements(step, tuple(gate_ids)))
        if previous_id is not None:
            requirements.insert(0, previous_id)
        state = _initial_state(step, submit_state, first=index == 1)
        graph.add_action(
            ActionNode(
                action_id=action_id,
                application_id=application_id,
                action_type=step.action_type,
                executor=step.executor,
                instruction=step.instruction,
                expected_output=_expected_output(step.action_type),
                requires=tuple(dict.fromkeys(requirements)),
                produces=(f"state:{application_id}:step:{index:02d}:complete",),
                next_actions=(action_ids[index],) if index < len(action_ids) else (),
                deadline=deadline,
                priority=_priority(row),
                state=state,
                idempotency_key=_idempotency_key(
                    application_id,
                    str(index),
                    step.action_type,
                    submit_state,
                    str(deadline or ""),
                    deadline_result.value,
                ),
                metadata={
                    "queue_id": str(row.get("Queue ID") or ""),
                    "opportunity_id": opportunity_id,
                    "title": str(row.get("Title") or ""),
                    "provider": str(row.get("Provider") or ""),
                    "role": str(row.get("Role") or ""),
                    "bucket": str(row.get("Bucket") or ""),
                    "submit_state": submit_state,
                    "source_next_action": next_action,
                    "deadline_gate": deadline_result.value,
                    "ordinal": index,
                    "step_count": len(steps),
                },
            )
        )
        previous_id = action_id

    graph.recompute(now)
    return graph


def compile_mass_apply_rows_atomic(
    rows: Iterable[Mapping[str, Any]], *, now: datetime | None = None
) -> RuntimeGraph:
    now = now or datetime.now(timezone.utc)
    _aware(now, "now")
    merged = RuntimeGraph()
    for row in rows:
        subgraph = compile_mass_apply_row_atomic(row, now=now)
        for gate in subgraph.gates.values():
            if gate.gate_id in merged.gates and merged.gates[gate.gate_id] != gate:
                raise ValueError(f"conflicting gate: {gate.gate_id}")
            merged.gates[gate.gate_id] = gate
        for action in subgraph.actions.values():
            if action.action_id in merged.actions:
                raise ValueError(f"duplicate action: {action.action_id}")
            merged.actions[action.action_id] = action
    merged.recompute(now)
    return merged


def decompose_next_action(raw: str) -> list[AtomicStep]:
    token = _normalise(raw)
    if not token:
        return [_agent("VERIFY_CURRENT_STATE")]

    if "CREATE_TCANET_ACCOUNT" in token and "SUBMIT" in token:
        return [
            _human("CREATE_TCANET_ACCOUNT"),
            _agent("CAPTURE_TCANET_FORM"),
            _human("PERSONALLY_COMPLETE_SUBMIT_STORE_RECEIPT"),
        ]

    if "CREATE_EYP_ESC_ACCOUNT" in token and "SUBMIT" in token:
        steps = [_human("CREATE_EYP_ESC_ACCOUNT")]
        if "INGEST_YUPI_REPLY" in token:
            steps.append(_agent("INGEST_YUPI_REPLY_VERIFY_CURRENT_ROUTE"))
        steps.append(_human("FINALISE_ASSETS_SUBMIT_CURRENT_ROUTE_STORE_RECEIPT"))
        return steps

    if "CREATE_EYP_ACCOUNT" in token and "SUBMIT" in token:
        return [
            _human("CREATE_EYP_ACCOUNT"),
            _agent("CHECK_HOST_REPLY_AND_HARD_GATES"),
            _human("CONFIRM_COMMITMENT_SUBMIT_STORE_RECEIPT"),
        ]

    if "OPEN_MYSALTO" in token and "SUBMIT" in token:
        return [
            _human("OPEN_MYSALTO_LOGIN_CAPTURE_QUESTIONS"),
            _agent("VERIFY_CURRENT_YOUTH_WORK_GATE"),
            _human("HUMAN_FINAL_SUBMIT_STORE_RECEIPT"),
        ]

    if "INGEST_PAYMENT_DETAILS" in token and "TRANSFER" in token:
        return [
            _agent("INGEST_PAYMENT_DETAILS_VERIFY_TERMS"),
            _human("HUMAN_APPROVE_OR_DECLINE_TRANSFER"),
        ]

    if token.startswith("OPEN_EXTERNAL_FORM") and "SUBMIT" in token:
        return [
            _agent("CAPTURE_EXTERNAL_FORM_AND_QUESTIONS"),
            _human("COMPLETE_AUTHENTIC_FINAL_SUBMIT_STORE_RECEIPT"),
        ]

    if token.startswith("OPEN_APPLICATION_PROCEDURE") and "SUBMIT" in token:
        return [
            _agent("CAPTURE_APPLICATION_PROCEDURE_AND_QUESTIONS"),
            _human("COMPLETE_AUTHENTIC_FINAL_SUBMIT_STORE_RECEIPT"),
        ]

    if token.startswith("CAPTURE_VRAR_APPLICATION_ROUTE") and "SUBMIT" in token:
        return [
            _agent("CAPTURE_VRAR_APPLICATION_ROUTE"),
            _human("COMPLETE_AUTHENTIC_FINAL_SUBMIT_STORE_RECEIPT"),
        ]

    if token.startswith("CAPTURE_FORM_QUESTIONS") and "SUBMIT" in token:
        return [
            _agent("CAPTURE_FORM_QUESTIONS"),
            _human("COMPLETE_HUMAN_FINAL_SUBMIT_STORE_RECEIPT"),
        ]

    fragments: list[str] = []
    for clause in raw.replace(";", "_THEN_").split("_THEN_"):
        clause = clause.strip(" _")
        if clause:
            fragments.append(clause)
    if len(fragments) > 1:
        return [_step(fragment) for fragment in fragments]

    return [_step(raw)]


def parse_live_gate_result(value: str | None, *, kind: str) -> GateResult:
    token = _normalise(value or "")
    if not token:
        return GateResult.UNKNOWN
    fail_tokens = (
        "HARD_FAIL",
        "HARD_REQUIREMENT_FAIL",
        "NOT_ELIGIBLE",
        "INELIGIBLE",
        "CALL_CLOSED",
        "DEADLINE_PASSED",
        "TERMINAL",
        "FULL_GROUP",
    )
    unknown_tokens = (
        "UNKNOWN",
        "PENDING",
        "VERIFY",
        "QUERY",
        "UNRESOLVED",
        "MISSING",
        "TBD",
        "TO_VERIFY",
        "CONFLICT",
        "PROVISIONAL",
        "LIKELY",
    )
    if any(part in token for part in fail_tokens):
        return GateResult.FAIL
    if any(part in token for part in unknown_tokens):
        return GateResult.UNKNOWN

    if kind == "form":
        pass_tokens = (
            "PASS",
            "CONFIRMED",
            "VERIFIED",
            "AI_ALLOWED",
            "AI_ASSIST_ONLY",
            "AI_NA",
            "APPLICATION_PROCEDURE",
            "PUBLIC_FORM",
            "FORM_KNOWN",
            "FORM_ROUTE_KNOWN",
            "EMAIL_ROUTE",
            "PORTAL_ROUTE",
            "OFFICIAL_ROUTE",
            "NO_FORM_REQUIRED",
            "INFOPACK_VERIFIED",
            "ROUTE_CAPTURED",
        )
    else:
        pass_tokens = (
            "PASS",
            "CONFIRMED",
            "VERIFIED",
            "ELIGIBLE",
            "LISTED",
            "SPAIN_PARTNER",
            "SPAIN_ROUTE",
            "MURCIA_SENDING_ROUTE",
            "EU_CITIZEN_ROUTE",
            "OPEN_INTERNATIONAL",
            "PROFILE_PASS",
            "PRIVATE_GATE_PASS",
            "SELECTED_BY_SENDING_ORG",
            "SPAIN_OFFICIAL_ROUTE",
            "SPAIN_COST_ROUTE_VERIFIED",
            "SPAIN_WAS_ELIGIBLE",
        )
    if any(part in token for part in pass_tokens):
        return GateResult.PASS
    return GateResult.UNKNOWN


def _deadline_gate(
    row: Mapping[str, Any], *, deadline: datetime | None, now: datetime
) -> tuple[GateResult, str]:
    evidence = _normalise(
        " | ".join(
            str(row.get(key) or "")
            for key in (
                "Bucket",
                "Role Gate",
                "Infopack/Form/AI",
                "Submit State",
                "Next Action",
            )
        )
    )
    override_tokens = (
        "HOST_AUTHORISED_LATE_APPLICATION",
        "LATE_ROUTE_AUTHORISED",
        "T0_SELECTED_HUMAN_CONFIRMATION",
        "SELECTED_NOT_CONFIRMED",
        "OPEN_PLACES_CONFIRMED",
        "DIRECT_ORG_OPEN_PLACES",
        "WAITING_HUMAN_PAYMENT_GATE",
    )
    if any(token in evidence for token in override_tokens):
        return GateResult.PASS, "Authoritative late/open/selected/payment-route evidence overrides the ordinary deadline gate."
    if deadline is None:
        return GateResult.UNKNOWN, f"Exact actionable deadline unresolved from source value: {row.get('Deadline')!s}"
    if deadline < now:
        return GateResult.FAIL, f"Deadline {deadline.isoformat()} is before runtime now {now.isoformat()}; verify extension/late route before human work."
    return GateResult.PASS, f"Deadline {deadline.isoformat()} is still open at runtime now {now.isoformat()}."


def _step(raw: str) -> AtomicStep:
    token = _normalise(raw)
    if _is_human(token):
        return _human(raw)
    if "TERMINAL_ARCHIVE" in token:
        return AtomicStep(raw, ExecutorType.SYSTEM, _instruction(raw))
    return _agent(raw)


def _is_human(token: str) -> bool:
    human_tokens = (
        "HUMAN_",
        "LOGIN",
        "CREATE_EYP_ACCOUNT",
        "CREATE_EYP_ESC_ACCOUNT",
        "CREATE_TCANET_ACCOUNT",
        "MFA",
        "2FA",
        "CAPTCHA",
        "PAY_",
        "PAYMENT",
        "TRANSFER",
        "RECORD",
        "VIDEO",
        "PERSONALLY_COMPLETE",
        "APPLICANT_OWNED",
        "CONFIRM_IDENTITY",
        "CONFIRM_TRUE",
        "SUBMIT",
    )
    return any(part in token for part in human_tokens)


def _is_irreversible(raw: str) -> bool:
    token = _normalise(raw)
    return any(part in token for part in ("SUBMIT", "PAY", "TRANSFER", "CONFIRM_IDENTITY"))


def _human(raw: str) -> AtomicStep:
    return AtomicStep(raw, ExecutorType.HUMAN, _instruction(raw))


def _agent(raw: str) -> AtomicStep:
    return AtomicStep(raw, ExecutorType.AGENT, _instruction(raw))


def _instruction(raw: str) -> str:
    return raw.replace("_", " ").replace(";", " →").strip().title()


def _gate_requirements(step: AtomicStep, gate_ids: tuple[str, ...]) -> tuple[str, ...]:
    token = _normalise(step.action_type)
    deadline_gate = gate_ids[3:4]
    if step.executor in {ExecutorType.AGENT, ExecutorType.SYSTEM}:
        return ()
    if any(part in token for part in ("LOGIN", "CREATE_EYP_ACCOUNT", "CREATE_EYP_ESC_ACCOUNT", "CREATE_TCANET_ACCOUNT", "MFA", "2FA", "CAPTCHA")):
        return deadline_gate
    if any(part in token for part in ("PAY", "PAYMENT", "TRANSFER")):
        return (*gate_ids[:2], *deadline_gate)
    if "SUBMIT" in token:
        return gate_ids
    return (*gate_ids[:2], *deadline_gate)


def _initial_state(step: AtomicStep, submit_state: str, *, first: bool) -> ActionState:
    if first and any(part in _normalise(step.action_type + " " + submit_state) for part in ("WAIT_HOST", "WAIT_ORGANISER", "WAIT_REPLY", "WAITING_EXTERNAL", "HOLD_EXTERNAL")):
        return ActionState.WAITING
    return ActionState.BLOCKED


def _terminal_submit_state(value: str) -> bool:
    token = _normalise(value)
    return any(part in token for part in ("CLOSED", "HARD_FAIL", "TERMINAL"))


def _expected_output(action_type: str) -> str:
    token = _normalise(action_type)
    if "SUBMIT" in token:
        return "submission_receipt_or_authoritative_confirmation"
    if any(part in token for part in ("PAY", "TRANSFER")):
        return "payment_receipt_and_terms"
    if any(part in token for part in ("VERIFY", "CAPTURE", "INGEST", "CHECK", "EXTRACT", "RETRIEVE", "RESOLVE")):
        return "source_backed_evidence_and_recomputed_gates"
    if any(part in token for part in ("LOGIN", "ACCOUNT")):
        return "authenticated_access_confirmation_without_credentials"
    if "VIDEO" in token:
        return "applicant_owned_video_asset"
    if "ARCHIVE" in token:
        return "terminal_state_preserved_with_evidence"
    return "verified_state_transition_evidence"


def _priority(row: Mapping[str, Any]) -> int:
    bucket = _normalise(str(row.get("Bucket") or ""))
    if bucket.startswith("T0"):
        return 100
    if bucket.startswith("T1"):
        return 90
    if bucket.startswith("T2"):
        return 75
    if bucket.startswith("T3"):
        return 60
    return 50


def _parse_deadline(raw: Any) -> datetime | None:
    if raw is None:
        return None
    value = str(raw).strip()
    upper = value.upper()
    if not value or upper == "ASAP" or "ROLLING" in upper or "TIME_UNKNOWN" in upper or "SOURCE_LITERAL" in upper:
        return None
    if value.replace(".", "", 1).isdigit():
        return None
    value = value.replace(" 23:59:00", "T23:59:00")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.fromisoformat(value + "T23:59:00+02:00")
        except ValueError:
            return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _idempotency_key(*parts: str) -> str:
    raw = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return "rgidem_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _required(row: Mapping[str, Any], key: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        raise ValueError(f"missing required row field: {key}")
    return value


def _normalise(value: str) -> str:
    return (value or "").upper().replace("-", "_")


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
