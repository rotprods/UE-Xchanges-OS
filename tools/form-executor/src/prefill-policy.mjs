const PREFILL_ALLOWED_STATES = new Set(['answer_pack_resolved', 'prefill_ready']);
const EDITABLE_OWNERSHIP = new Set(['green_agent_factual', 'yellow_agent_assisted_human_review']);
const PLAN_BLOCKING_OWNERSHIP = new Set(['black_secret_or_never_model', 'unresolved']);
const SUPPORTED_TYPES = new Set(['text', 'textarea', 'email', 'number', 'date', 'select', 'radio', 'checkbox']);
const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '[::1]']);

export function assertLoopbackUrl(value) {
  const parsed = new URL(value);
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('prefill URL must use http or https');
  if (!LOOPBACK_HOSTS.has(parsed.hostname)) {
    throw new Error('PREFILL_LOCAL development mode rejects non-loopback origins');
  }
  return parsed;
}

function assertIsoFuture(value, now) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) throw new Error('plan expires_at must be an ISO date-time');
  if (parsed.getTime() <= now.getTime()) throw new Error('execution plan is expired');
}

export function validateLocalPrefillPlan(plan, { now = new Date() } = {}) {
  if (!plan || typeof plan !== 'object' || Array.isArray(plan)) throw new Error('plan must be an object');
  for (const key of ['plan_id', 'application_id', 'opportunity_id', 'canonical_form_url', 'provider', 'form_fingerprint', 'state', 'expires_at']) {
    if (typeof plan[key] !== 'string' || !plan[key].trim()) throw new Error(`plan ${key} must be non-empty`);
  }
  const parsedUrl = assertLoopbackUrl(plan.canonical_form_url);
  if (!PREFILL_ALLOWED_STATES.has(plan.state)) throw new Error('plan state is not prefill-ready');
  assertIsoFuture(plan.expires_at, now);
  if (!Array.isArray(plan.fields) || plan.fields.length === 0) throw new Error('plan fields must not be empty');
  if (Array.isArray(plan.attachments) && plan.attachments.length) {
    throw new Error('file attachments are not supported by PREFILL_LOCAL');
  }

  const seen = new Set();
  const writes = [];
  const protectedFields = [];
  for (const field of plan.fields) {
    if (!field || typeof field !== 'object') throw new Error('every field must be an object');
    if (typeof field.field_key !== 'string' || !field.field_key.trim()) throw new Error('field_key must be non-empty');
    if (seen.has(field.field_key)) throw new Error(`duplicate field_key: ${field.field_key}`);
    seen.add(field.field_key);

    const editable = field.editable_by_agent === true;
    const ownership = field.ownership;
    const sensitivity = field.sensitivity;
    if (PLAN_BLOCKING_OWNERSHIP.has(ownership)) {
      throw new Error(`prefill-ready plan cannot contain ${ownership}: ${field.field_key}`);
    }
    if (editable) {
      if (!EDITABLE_OWNERSHIP.has(ownership)) throw new Error(`editable field has forbidden ownership: ${field.field_key}`);
      if (sensitivity === 'secret') throw new Error(`editable field cannot be SECRET: ${field.field_key}`);
      if (!SUPPORTED_TYPES.has(field.field_type)) throw new Error(`unsupported editable field type: ${field.field_key}`);
      if (field.answer === null || field.answer === undefined) throw new Error(`editable field has no answer: ${field.field_key}`);
      if (field.field_type === 'checkbox' && !(typeof field.answer === 'boolean' || Array.isArray(field.answer))) {
        throw new Error(`checkbox answer must be boolean or array: ${field.field_key}`);
      }
      if (field.field_type === 'radio' && typeof field.answer !== 'string') {
        throw new Error(`radio answer must be string: ${field.field_key}`);
      }
      writes.push({ field_key: field.field_key, field_type: field.field_type, answer: field.answer });
    } else {
      protectedFields.push(field.field_key);
    }
  }
  if (!writes.length) throw new Error('plan has no agent-editable fields');
  return { origin: parsedUrl.origin, writes, protectedFields };
}
