-- UE-Xchanges-OS Atomic Coordination Arbiter v1
--
-- Multi-host exclusion and at-most-once external-effect ledger.
-- This schema is deliberately small: it is not a second CRM or RuntimeGraph.
-- All timestamps and lease expiry decisions use the PostgreSQL clock.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS uex_arbiter;

CREATE SEQUENCE IF NOT EXISTS uex_arbiter.fencing_token_seq AS bigint START 1;

CREATE TABLE IF NOT EXISTS uex_arbiter.agent_sessions (
    session_id text PRIMARY KEY,
    agent_id text NOT NULL CHECK (btrim(agent_id) <> ''),
    status text NOT NULL CHECK (status IN ('ACTIVE', 'READ_ONLY', 'HANDOFF_READY', 'COMPLETED', 'FAILED')),
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    heartbeat_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    observed_main_sha text NOT NULL CHECK (btrim(observed_main_sha) <> ''),
    bootstrap_version text NOT NULL CHECK (btrim(bootstrap_version) <> ''),
    capabilities jsonb NOT NULL DEFAULT '{}'::jsonb,
    CHECK (btrim(session_id) <> ''),
    CHECK (heartbeat_at >= started_at)
);

CREATE TABLE IF NOT EXISTS uex_arbiter.work_leases (
    lease_id text PRIMARY KEY,
    owner_session_id text NOT NULL REFERENCES uex_arbiter.agent_sessions(session_id),
    owner_agent_id text NOT NULL CHECK (btrim(owner_agent_id) <> ''),
    fencing_token bigint NOT NULL UNIQUE,
    scope_hash text NOT NULL CHECK (scope_hash ~ '^[0-9a-f]{64}$'),
    scopes text[] NOT NULL CHECK (cardinality(scopes) > 0),
    expected_revision text NOT NULL CHECK (btrim(expected_revision) <> ''),
    state text NOT NULL CHECK (state IN ('ACTIVE', 'RELEASED', 'EXPIRED')),
    acquired_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    heartbeat_at timestamptz NOT NULL,
    release_reason text NOT NULL DEFAULT '',
    CHECK (btrim(lease_id) <> ''),
    CHECK (expires_at > acquired_at),
    CHECK (heartbeat_at >= acquired_at)
);

CREATE UNIQUE INDEX IF NOT EXISTS work_leases_one_active_per_session
    ON uex_arbiter.work_leases(owner_session_id)
    WHERE state = 'ACTIVE';

CREATE INDEX IF NOT EXISTS work_leases_active_expiry
    ON uex_arbiter.work_leases(state, expires_at);

CREATE TABLE IF NOT EXISTS uex_arbiter.scope_owners (
    scope_key text PRIMARY KEY CHECK (btrim(scope_key) <> ''),
    lease_id text NOT NULL REFERENCES uex_arbiter.work_leases(lease_id) ON DELETE CASCADE,
    fencing_token bigint NOT NULL,
    expires_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS scope_owners_lease_id
    ON uex_arbiter.scope_owners(lease_id);

CREATE TABLE IF NOT EXISTS uex_arbiter.external_effects (
    effect_key text PRIMARY KEY CHECK (btrim(effect_key) <> ''),
    effect_type text NOT NULL CHECK (btrim(effect_type) <> ''),
    application_id text NOT NULL CHECK (btrim(application_id) <> ''),
    organisation_id text NOT NULL DEFAULT '',
    provider text NOT NULL DEFAULT '',
    provider_target text NOT NULL DEFAULT '',
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    initiator_session_id text NOT NULL REFERENCES uex_arbiter.agent_sessions(session_id),
    initiator_lease_id text NOT NULL REFERENCES uex_arbiter.work_leases(lease_id),
    initiator_fencing_token bigint NOT NULL,
    state text NOT NULL CHECK (state IN (
        'RESERVED', 'STARTED', 'CONFIRMED', 'FAILED_NO_EFFECT',
        'UNCERTAIN', 'CANCELLED_BEFORE_START'
    )),
    attempt_no integer NOT NULL CHECK (attempt_no >= 1),
    reserved_at timestamptz NOT NULL,
    started_at timestamptz,
    resolved_at timestamptz,
    provider_ref text NOT NULL DEFAULT '',
    receipt_ref text NOT NULL DEFAULT '',
    failure_code text NOT NULL DEFAULT '',
    reconciliation_ref text NOT NULL DEFAULT '',
    resolved_by_session_id text REFERENCES uex_arbiter.agent_sessions(session_id),
    resolved_by_lease_id text REFERENCES uex_arbiter.work_leases(lease_id),
    resolved_by_fencing_token bigint
);

CREATE INDEX IF NOT EXISTS external_effects_application
    ON uex_arbiter.external_effects(application_id, state);

CREATE TABLE IF NOT EXISTS uex_arbiter.coordination_outbox (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    idempotency_key text NOT NULL UNIQUE CHECK (btrim(idempotency_key) <> ''),
    event_type text NOT NULL CHECK (btrim(event_type) <> ''),
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    mirrored_to_drive_at timestamptz
);

CREATE OR REPLACE FUNCTION uex_arbiter.register_agent_session(
    p_session_id text,
    p_agent_id text,
    p_observed_main_sha text,
    p_bootstrap_version text,
    p_capabilities jsonb DEFAULT '{}'::jsonb
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
BEGIN
    IF btrim(coalesce(p_session_id, '')) = '' OR btrim(coalesce(p_agent_id, '')) = '' THEN
        RAISE EXCEPTION 'SESSION_ID_AND_AGENT_ID_REQUIRED';
    END IF;
    IF btrim(coalesce(p_observed_main_sha, '')) = '' OR btrim(coalesce(p_bootstrap_version, '')) = '' THEN
        RAISE EXCEPTION 'MAIN_SHA_AND_BOOTSTRAP_VERSION_REQUIRED';
    END IF;

    INSERT INTO agent_sessions(
        session_id, agent_id, status, started_at, heartbeat_at,
        observed_main_sha, bootstrap_version, capabilities
    ) VALUES (
        p_session_id, p_agent_id, 'ACTIVE', v_now, v_now,
        p_observed_main_sha, p_bootstrap_version, coalesce(p_capabilities, '{}'::jsonb)
    );

    INSERT INTO coordination_outbox(idempotency_key, event_type, payload)
    VALUES (
        'SESSION_STARTED:' || p_session_id,
        'SESSION_STARTED',
        jsonb_build_object('session_id', p_session_id, 'agent_id', p_agent_id)
    );
END;
$$;

CREATE OR REPLACE FUNCTION uex_arbiter.assert_active_fence(
    p_lease_id text,
    p_session_id text,
    p_fencing_token bigint,
    p_application_id text DEFAULT NULL
) RETURNS uex_arbiter.work_leases
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_lease uex_arbiter.work_leases%ROWTYPE;
    v_required_scope text;
BEGIN
    SELECT * INTO v_lease
      FROM work_leases
     WHERE lease_id = p_lease_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'LEASE_NOT_FOUND';
    END IF;
    IF v_lease.owner_session_id <> p_session_id THEN
        RAISE EXCEPTION 'LEASE_OWNER_MISMATCH';
    END IF;
    IF v_lease.fencing_token <> p_fencing_token THEN
        RAISE EXCEPTION 'STALE_FENCING_TOKEN';
    END IF;
    IF v_lease.state <> 'ACTIVE' OR v_lease.expires_at <= v_now THEN
        RAISE EXCEPTION 'LEASE_NOT_ACTIVE';
    END IF;

    IF p_application_id IS NOT NULL THEN
        v_required_scope := 'APPLICATION:' || p_application_id;
        IF NOT (v_required_scope = ANY(v_lease.scopes)) THEN
            RAISE EXCEPTION 'APPLICATION_SCOPE_REQUIRED:%', v_required_scope;
        END IF;
    END IF;

    RETURN v_lease;
END;
$$;

CREATE OR REPLACE FUNCTION uex_arbiter.claim_scope_set(
    p_lease_id text,
    p_session_id text,
    p_scopes text[],
    p_expected_revision text,
    p_ttl_seconds integer DEFAULT 900
) RETURNS TABLE(
    lease_id text,
    fencing_token bigint,
    scope_hash text,
    expires_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_scopes text[];
    v_scope text;
    v_scope_hash text;
    v_conflict text;
    v_agent_id text;
    v_token bigint;
    v_expires timestamptz;
BEGIN
    IF btrim(coalesce(p_lease_id, '')) = '' OR btrim(coalesce(p_expected_revision, '')) = '' THEN
        RAISE EXCEPTION 'LEASE_ID_AND_EXPECTED_REVISION_REQUIRED';
    END IF;
    IF p_ttl_seconds < 5 OR p_ttl_seconds > 3600 THEN
        RAISE EXCEPTION 'LEASE_TTL_OUT_OF_RANGE';
    END IF;
    IF coalesce(cardinality(p_scopes), 0) = 0 THEN
        RAISE EXCEPTION 'NONEMPTY_SCOPE_SET_REQUIRED';
    END IF;

    SELECT array_agg(s ORDER BY s)
      INTO v_scopes
      FROM (
        SELECT DISTINCT btrim(x) AS s
          FROM unnest(p_scopes) AS x
         WHERE btrim(x) <> ''
      ) q;

    IF v_scopes IS NULL OR cardinality(v_scopes) <> cardinality(p_scopes) THEN
        RAISE EXCEPTION 'SCOPE_SET_MUST_BE_NONEMPTY_UNIQUE';
    END IF;

    -- Deterministic lock order prevents opposite-order multi-scope deadlocks.
    FOREACH v_scope IN ARRAY v_scopes LOOP
        PERFORM pg_advisory_xact_lock(hashtextextended(v_scope, 0));
    END LOOP;

    SELECT agent_id INTO v_agent_id
      FROM agent_sessions
     WHERE session_id = p_session_id
       AND status = 'ACTIVE'
     FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'ACTIVE_SESSION_REQUIRED';
    END IF;

    -- Expiry is derived only from the database clock; textual ACTIVE is not enough.
    UPDATE work_leases
       SET state = 'EXPIRED'
     WHERE state = 'ACTIVE'
       AND expires_at <= v_now;

    DELETE FROM scope_owners so
     USING work_leases wl
     WHERE so.lease_id = wl.lease_id
       AND wl.state <> 'ACTIVE';

    IF EXISTS (
        SELECT 1 FROM work_leases
         WHERE owner_session_id = p_session_id
           AND state = 'ACTIVE'
           AND expires_at > v_now
    ) THEN
        RAISE EXCEPTION 'SESSION_ALREADY_HAS_ACTIVE_LEASE';
    END IF;

    SELECT so.scope_key INTO v_conflict
      FROM scope_owners so
      JOIN work_leases wl ON wl.lease_id = so.lease_id
     WHERE so.scope_key = ANY(v_scopes)
       AND wl.state = 'ACTIVE'
       AND wl.expires_at > v_now
     ORDER BY so.scope_key
     LIMIT 1;

    IF v_conflict IS NOT NULL THEN
        RAISE EXCEPTION 'SCOPE_CONFLICT:%', v_conflict;
    END IF;

    v_scope_hash := encode(digest(array_to_string(v_scopes, chr(31)), 'sha256'), 'hex');
    v_token := nextval('fencing_token_seq');
    v_expires := v_now + make_interval(secs => p_ttl_seconds);

    INSERT INTO work_leases(
        lease_id, owner_session_id, owner_agent_id, fencing_token,
        scope_hash, scopes, expected_revision, state,
        acquired_at, expires_at, heartbeat_at
    ) VALUES (
        p_lease_id, p_session_id, v_agent_id, v_token,
        v_scope_hash, v_scopes, p_expected_revision, 'ACTIVE',
        v_now, v_expires, v_now
    );

    INSERT INTO scope_owners(scope_key, lease_id, fencing_token, expires_at)
    SELECT s, p_lease_id, v_token, v_expires
      FROM unnest(v_scopes) AS s;

    INSERT INTO coordination_outbox(idempotency_key, event_type, payload)
    VALUES (
        'LEASE_ACQUIRED:' || p_lease_id,
        'LEASE_ACQUIRED',
        jsonb_build_object(
            'lease_id', p_lease_id,
            'owner_session_id', p_session_id,
            'fencing_token', v_token,
            'scope_hash', v_scope_hash,
            'scopes', to_jsonb(v_scopes),
            'expires_at', v_expires
        )
    );

    RETURN QUERY SELECT p_lease_id, v_token, v_scope_hash, v_expires;
END;
$$;

CREATE OR REPLACE FUNCTION uex_arbiter.heartbeat_lease(
    p_lease_id text,
    p_session_id text,
    p_fencing_token bigint,
    p_ttl_seconds integer DEFAULT 900
) RETURNS timestamptz
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_expires timestamptz;
    v_lease uex_arbiter.work_leases%ROWTYPE;
BEGIN
    IF p_ttl_seconds < 5 OR p_ttl_seconds > 3600 THEN
        RAISE EXCEPTION 'LEASE_TTL_OUT_OF_RANGE';
    END IF;
    v_lease := assert_active_fence(p_lease_id, p_session_id, p_fencing_token, NULL);
    v_expires := v_now + make_interval(secs => p_ttl_seconds);

    UPDATE work_leases
       SET heartbeat_at = v_now, expires_at = v_expires
     WHERE lease_id = p_lease_id
       AND fencing_token = p_fencing_token
       AND state = 'ACTIVE';

    UPDATE scope_owners
       SET expires_at = v_expires
     WHERE lease_id = p_lease_id
       AND fencing_token = p_fencing_token;

    UPDATE agent_sessions
       SET heartbeat_at = v_now
     WHERE session_id = p_session_id;

    RETURN v_expires;
END;
$$;

CREATE OR REPLACE FUNCTION uex_arbiter.release_lease(
    p_lease_id text,
    p_session_id text,
    p_fencing_token bigint,
    p_reason text
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_lease uex_arbiter.work_leases%ROWTYPE;
BEGIN
    IF btrim(coalesce(p_reason, '')) = '' THEN
        RAISE EXCEPTION 'RELEASE_REASON_REQUIRED';
    END IF;
    v_lease := assert_active_fence(p_lease_id, p_session_id, p_fencing_token, NULL);

    UPDATE work_leases
       SET state = 'RELEASED', heartbeat_at = v_now, release_reason = p_reason
     WHERE lease_id = p_lease_id
       AND fencing_token = p_fencing_token
       AND state = 'ACTIVE';

    DELETE FROM scope_owners
     WHERE lease_id = p_lease_id
       AND fencing_token = p_fencing_token;

    INSERT INTO coordination_outbox(idempotency_key, event_type, payload)
    VALUES (
        'LEASE_RELEASED:' || p_lease_id,
        'LEASE_RELEASED',
        jsonb_build_object(
            'lease_id', p_lease_id,
            'owner_session_id', p_session_id,
            'fencing_token', p_fencing_token,
            'reason', p_reason
        )
    );
END;
$$;

CREATE OR REPLACE FUNCTION uex_arbiter.reserve_external_effect(
    p_effect_key text,
    p_effect_type text,
    p_application_id text,
    p_organisation_id text,
    p_provider text,
    p_provider_target text,
    p_payload_sha256 text,
    p_lease_id text,
    p_session_id text,
    p_fencing_token bigint
) RETURNS TABLE(state text, attempt_no integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_old uex_arbiter.external_effects%ROWTYPE;
    v_attempt integer;
BEGIN
    IF btrim(coalesce(p_effect_key, '')) = '' OR btrim(coalesce(p_effect_type, '')) = '' THEN
        RAISE EXCEPTION 'EFFECT_KEY_AND_TYPE_REQUIRED';
    END IF;
    IF btrim(coalesce(p_application_id, '')) = '' THEN
        RAISE EXCEPTION 'APPLICATION_ID_REQUIRED';
    END IF;
    IF coalesce(p_payload_sha256, '') !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION 'PAYLOAD_SHA256_REQUIRED';
    END IF;

    PERFORM assert_active_fence(p_lease_id, p_session_id, p_fencing_token, p_application_id);

    SELECT * INTO v_old
      FROM external_effects
     WHERE effect_key = p_effect_key
     FOR UPDATE;

    IF NOT FOUND THEN
        v_attempt := 1;
        INSERT INTO external_effects(
            effect_key, effect_type, application_id, organisation_id,
            provider, provider_target, payload_sha256,
            initiator_session_id, initiator_lease_id, initiator_fencing_token,
            state, attempt_no, reserved_at
        ) VALUES (
            p_effect_key, p_effect_type, p_application_id, coalesce(p_organisation_id, ''),
            coalesce(p_provider, ''), coalesce(p_provider_target, ''), p_payload_sha256,
            p_session_id, p_lease_id, p_fencing_token,
            'RESERVED', v_attempt, v_now
        );
    ELSE
        IF v_old.state NOT IN ('FAILED_NO_EFFECT', 'CANCELLED_BEFORE_START') THEN
            RAISE EXCEPTION 'EFFECT_BLOCKED:%', v_old.state;
        END IF;
        v_attempt := v_old.attempt_no + 1;
        UPDATE external_effects
           SET effect_type = p_effect_type,
               application_id = p_application_id,
               organisation_id = coalesce(p_organisation_id, ''),
               provider = coalesce(p_provider, ''),
               provider_target = coalesce(p_provider_target, ''),
               payload_sha256 = p_payload_sha256,
               initiator_session_id = p_session_id,
               initiator_lease_id = p_lease_id,
               initiator_fencing_token = p_fencing_token,
               state = 'RESERVED',
               attempt_no = v_attempt,
               reserved_at = v_now,
               started_at = NULL,
               resolved_at = NULL,
               provider_ref = '', receipt_ref = '', failure_code = '', reconciliation_ref = '',
               resolved_by_session_id = NULL, resolved_by_lease_id = NULL,
               resolved_by_fencing_token = NULL
         WHERE effect_key = p_effect_key;
    END IF;

    INSERT INTO coordination_outbox(idempotency_key, event_type, payload)
    VALUES (
        'EFFECT_RESERVED:' || p_effect_key || ':' || v_attempt::text,
        'EXTERNAL_EFFECT_RESERVED',
        jsonb_build_object(
            'effect_key', p_effect_key,
            'effect_type', p_effect_type,
            'application_id', p_application_id,
            'attempt_no', v_attempt,
            'lease_id', p_lease_id,
            'fencing_token', p_fencing_token,
            'payload_sha256', p_payload_sha256
        )
    );

    RETURN QUERY SELECT 'RESERVED'::text, v_attempt;
END;
$$;

CREATE OR REPLACE FUNCTION uex_arbiter.mark_effect_started(
    p_effect_key text,
    p_lease_id text,
    p_session_id text,
    p_fencing_token bigint
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_application_id text;
    v_effect uex_arbiter.external_effects%ROWTYPE;
BEGIN
    SELECT application_id INTO v_application_id
      FROM external_effects
     WHERE effect_key = p_effect_key;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'EFFECT_NOT_FOUND';
    END IF;

    PERFORM assert_active_fence(p_lease_id, p_session_id, p_fencing_token, v_application_id);

    SELECT * INTO v_effect
      FROM external_effects
     WHERE effect_key = p_effect_key
     FOR UPDATE;

    IF v_effect.state <> 'RESERVED' THEN
        RAISE EXCEPTION 'EFFECT_START_REQUIRES_RESERVED:%', v_effect.state;
    END IF;
    IF v_effect.initiator_lease_id <> p_lease_id
       OR v_effect.initiator_session_id <> p_session_id
       OR v_effect.initiator_fencing_token <> p_fencing_token THEN
        RAISE EXCEPTION 'EFFECT_INITIATOR_FENCE_MISMATCH';
    END IF;

    UPDATE external_effects
       SET state = 'STARTED', started_at = v_now
     WHERE effect_key = p_effect_key
       AND state = 'RESERVED';

    INSERT INTO coordination_outbox(idempotency_key, event_type, payload)
    VALUES (
        'EFFECT_STARTED:' || p_effect_key || ':' || v_effect.attempt_no::text,
        'EXTERNAL_EFFECT_STARTED',
        jsonb_build_object(
            'effect_key', p_effect_key,
            'application_id', v_application_id,
            'attempt_no', v_effect.attempt_no,
            'lease_id', p_lease_id,
            'fencing_token', p_fencing_token
        )
    );
END;
$$;

CREATE OR REPLACE FUNCTION uex_arbiter.cancel_reserved_effect(
    p_effect_key text,
    p_lease_id text,
    p_session_id text,
    p_fencing_token bigint,
    p_evidence_ref text
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_application_id text;
    v_attempt integer;
    v_state text;
BEGIN
    IF btrim(coalesce(p_evidence_ref, '')) = '' THEN
        RAISE EXCEPTION 'EVIDENCE_REF_REQUIRED';
    END IF;
    SELECT application_id, attempt_no, state
      INTO v_application_id, v_attempt, v_state
      FROM external_effects
     WHERE effect_key = p_effect_key
     FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'EFFECT_NOT_FOUND';
    END IF;

    PERFORM assert_active_fence(p_lease_id, p_session_id, p_fencing_token, v_application_id);
    IF v_state <> 'RESERVED' THEN
        RAISE EXCEPTION 'CANCEL_REQUIRES_RESERVED:%', v_state;
    END IF;

    UPDATE external_effects
       SET state = 'CANCELLED_BEFORE_START', resolved_at = v_now,
           reconciliation_ref = p_evidence_ref,
           resolved_by_session_id = p_session_id,
           resolved_by_lease_id = p_lease_id,
           resolved_by_fencing_token = p_fencing_token
     WHERE effect_key = p_effect_key
       AND state = 'RESERVED';

    INSERT INTO coordination_outbox(idempotency_key, event_type, payload)
    VALUES (
        'EFFECT_CANCELLED:' || p_effect_key || ':' || v_attempt::text,
        'EXTERNAL_EFFECT_CANCELLED_BEFORE_START',
        jsonb_build_object('effect_key', p_effect_key, 'attempt_no', v_attempt, 'evidence_ref', p_evidence_ref)
    );
END;
$$;

CREATE OR REPLACE FUNCTION uex_arbiter.resolve_external_effect(
    p_effect_key text,
    p_resolution text,
    p_lease_id text,
    p_session_id text,
    p_fencing_token bigint,
    p_evidence_ref text,
    p_provider_ref text DEFAULT '',
    p_receipt_ref text DEFAULT '',
    p_failure_code text DEFAULT ''
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = uex_arbiter, pg_temp
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_application_id text;
    v_attempt integer;
    v_state text;
BEGIN
    IF p_resolution NOT IN ('CONFIRMED', 'FAILED_NO_EFFECT', 'UNCERTAIN') THEN
        RAISE EXCEPTION 'INVALID_EFFECT_RESOLUTION';
    END IF;
    IF btrim(coalesce(p_evidence_ref, '')) = '' THEN
        RAISE EXCEPTION 'EVIDENCE_REF_REQUIRED';
    END IF;

    SELECT application_id, attempt_no, state
      INTO v_application_id, v_attempt, v_state
      FROM external_effects
     WHERE effect_key = p_effect_key
     FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'EFFECT_NOT_FOUND';
    END IF;

    PERFORM assert_active_fence(p_lease_id, p_session_id, p_fencing_token, v_application_id);

    IF v_state = 'STARTED' THEN
        NULL;
    ELSIF v_state = 'UNCERTAIN' AND p_resolution IN ('CONFIRMED', 'FAILED_NO_EFFECT') THEN
        NULL;
    ELSE
        RAISE EXCEPTION 'INVALID_EFFECT_TRANSITION:%->%', v_state, p_resolution;
    END IF;

    IF p_resolution = 'CONFIRMED'
       AND btrim(coalesce(p_provider_ref, '')) = ''
       AND btrim(coalesce(p_receipt_ref, '')) = '' THEN
        RAISE EXCEPTION 'CONFIRMED_EFFECT_REQUIRES_PROVIDER_OR_RECEIPT_REF';
    END IF;

    UPDATE external_effects
       SET state = p_resolution,
           resolved_at = v_now,
           provider_ref = coalesce(p_provider_ref, ''),
           receipt_ref = coalesce(p_receipt_ref, ''),
           failure_code = coalesce(p_failure_code, ''),
           reconciliation_ref = p_evidence_ref,
           resolved_by_session_id = p_session_id,
           resolved_by_lease_id = p_lease_id,
           resolved_by_fencing_token = p_fencing_token
     WHERE effect_key = p_effect_key;

    INSERT INTO coordination_outbox(idempotency_key, event_type, payload)
    VALUES (
        'EFFECT_RESOLVED:' || p_effect_key || ':' || v_attempt::text || ':' || p_resolution,
        'EXTERNAL_EFFECT_' || p_resolution,
        jsonb_build_object(
            'effect_key', p_effect_key,
            'application_id', v_application_id,
            'attempt_no', v_attempt,
            'state_before', v_state,
            'state_after', p_resolution,
            'evidence_ref', p_evidence_ref,
            'provider_ref', coalesce(p_provider_ref, ''),
            'receipt_ref', coalesce(p_receipt_ref, ''),
            'failure_code', coalesce(p_failure_code, ''),
            'resolved_by_session_id', p_session_id,
            'resolved_by_lease_id', p_lease_id,
            'resolved_by_fencing_token', p_fencing_token
        )
    );
END;
$$;

-- Public/anonymous SQL callers receive no rights by default. Production grants are
-- a deployment concern and must go only to the dedicated trusted server role.
REVOKE ALL ON SCHEMA uex_arbiter FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA uex_arbiter FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA uex_arbiter FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA uex_arbiter FROM PUBLIC;
