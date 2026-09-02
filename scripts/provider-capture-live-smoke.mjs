#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ProviderCaptureService } from '../services/browser-worker/src/provider-capture.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'config/form-providers/google-forms-inspect-v1.json'), 'utf8'));
const url = process.env.UEX_PROVIDER_CAPTURE_SMOKE_URL;
if (!url) throw new Error('UEX_PROVIDER_CAPTURE_SMOKE_URL_REQUIRED');

const service = new ProviderCaptureService({ channel: 'chromium', headless: true });
const result = await service.inspect({
  applicationId: 'app-game-nature-v1',
  provider: 'google_forms',
  url,
  allowedOrigins: manifest.allowed_origins,
});

assert.equal(result.mode, 'INSPECT_PROVIDER_READ_ONLY');
assert.equal(result.application_id, 'app-game-nature-v1');
assert.equal(result.provider, 'google_forms');
assert.equal(result.safety.ephemeral_context, true);
assert.equal(result.safety.form_values_read, false);
assert.equal(result.safety.answer_values_exported, false);
assert.equal(result.safety.external_prefill_available, false);
assert.equal(result.safety.submit_available, false);
assert.ok(result.fields.length >= 3, `expected >=3 captured questions, got ${result.fields.length}`);
assert.match(result.form_fingerprint, /^sha256:[0-9a-f]{64}$/);

process.stdout.write(`${JSON.stringify({
  status: 'PASS',
  provider: result.provider,
  extraction_source: result.extraction_source || null,
  question_count: result.fields.length,
  required_count: result.fields.filter((field) => field.required).length,
  custom_count: result.unsupported_custom_control_count,
  form_fingerprint: result.form_fingerprint,
  validation_signature: result.validation_signature,
  fields: result.fields,
  safety: result.safety,
}, null, 2)}\n`);
