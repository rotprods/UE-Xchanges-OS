import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CONFIG_DIR = path.resolve(HERE, '../../../config/form-providers');
const PROVIDER_FILES = new Map([
  ['google_forms', 'google-forms-inspect-v1.json'],
]);

function origin(value) {
  const parsed = new URL(value);
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) {
    throw new Error('RELAY_PROVIDER_ORIGIN_INVALID');
  }
  return parsed.origin.toLowerCase();
}

export function loadProviderInspectManifest(providerId, configDir = CONFIG_DIR) {
  if (!PROVIDER_FILES.has(providerId)) throw new Error('RELAY_PROVIDER_NOT_CERTIFIED');
  const raw = JSON.parse(fs.readFileSync(path.join(configDir, PROVIDER_FILES.get(providerId)), 'utf8'));
  if (raw.provider_id !== providerId || raw.inspect_allowed !== true) throw new Error('RELAY_PROVIDER_INSPECT_NOT_CERTIFIED');
  if (raw.prefill_certified || raw.submit_certified) throw new Error('RELAY_PROVIDER_CAPTURE_MANIFEST_MUST_BE_READ_ONLY');
  if (!Array.isArray(raw.allowed_origins) || raw.allowed_origins.length === 0) throw new Error('RELAY_PROVIDER_ORIGINS_INVALID');
  return {
    provider_id: providerId,
    manifest_version: String(raw.manifest_version),
    allowed_origins: [...new Set(raw.allowed_origins.map(origin))],
    evidence_refs: Array.isArray(raw.evidence_refs) ? raw.evidence_refs.map(String) : [],
  };
}

export function assertProviderCaptureUrl(manifest, url) {
  const parsed = new URL(url);
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password || parsed.hash) throw new Error('RELAY_PROVIDER_TARGET_INVALID');
  if (!manifest.allowed_origins.includes(parsed.origin.toLowerCase())) throw new Error('RELAY_PROVIDER_TARGET_ORIGIN_NOT_CERTIFIED');
  return url;
}
