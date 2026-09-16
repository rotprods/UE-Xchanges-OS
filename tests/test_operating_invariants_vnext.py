from pathlib import Path


POLICY = Path("docs/OPERATING_POLICY_VNEXT.md")


def _policy() -> str:
    return POLICY.read_text(encoding="utf-8")


def test_runtimegraph_is_derived_not_authority():
    text = _policy()
    assert "RuntimeGraph is disposable/rebuildable derived state" in text
    assert "MUST NOT resurrect an action" in text


def test_terminal_states_cannot_emit_zombie_actions():
    text = _policy()
    for state in (
        "DECLINED",
        "EXPIRED",
        "CLOSED_WITHOUT_APPLICATION",
        "REJECTED",
        "ATTENDED",
        "COMPLETED",
    ):
        assert state in text
    assert "produce no application/payment/contact action" in text


def test_receipt_confirmed_blocks_resubmit():
    text = _policy()
    assert "`RECEIPT_CONFIRMED` forbids resubmission" in text
    assert "forbid automatic resubmit" in text


def test_executor_completed_does_not_mean_submitted():
    text = _policy()
    assert "Executor/process completion is not submission completion" in text
    assert "PARTIAL_EXECUTION" in text
    assert "RECEIPT_OBSERVED" in text


def test_apply_first_and_contact_budget_are_explicit():
    text = _policy()
    assert "prefer applying over emailing for redundant clarification" in text
    assert "Default contact budget" in text


def test_cv_separates_completed_from_applied():
    text = _policy()
    assert "ATTENDED_COMPLETED" in text
    assert "ACCEPTED_UPCOMING" in text
    assert "APPLIED_WAITING" in text
    assert "Only attended/completed projects" in text
