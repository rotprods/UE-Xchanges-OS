import path from 'node:path';
import os from 'node:os';

export const INSPECT_ONLY_SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);

export function normalizeOrigin(value) {
  const parsed = new URL(value);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('origin must use http or https');
  }
  return parsed.origin.toLowerCase();
}

export function normalizeAllowedOrigins(values) {
  if (!Array.isArray(values) || values.length === 0) {
    throw new Error('allowed origins must not be empty');
  }
  return [...new Set(values.map(normalizeOrigin))];
}

export function networkDecision({ method, url, isTopLevelNavigation, allowedOrigins }) {
  const normalizedMethod = String(method || '').toUpperCase();
  if (!INSPECT_ONLY_SAFE_METHODS.has(normalizedMethod)) {
    return { action: 'abort', reason: 'mutating_http_method' };
  }
  if (isTopLevelNavigation) {
    const origin = normalizeOrigin(url);
    if (!normalizeAllowedOrigins(allowedOrigins).includes(origin)) {
      return { action: 'abort', reason: 'top_level_origin_not_allowed' };
    }
  }
  return { action: 'continue', reason: 'inspect_only_safe_request' };
}

export function defaultProfileDir(homeDir = os.homedir()) {
  return path.join(homeDir, '.uexchanges', 'browser', 'profile');
}

export function assertDedicatedProfileDir(profileDir, homeDir = os.homedir()) {
  const resolved = path.resolve(profileDir);
  const dangerous = [
    path.join(homeDir, 'Library', 'Application Support', 'Google', 'Chrome'),
    path.join(homeDir, 'Library', 'Application Support', 'Chromium'),
    path.join(homeDir, 'Library', 'Application Support', 'Microsoft Edge'),
    path.join(homeDir, '.config', 'google-chrome'),
    path.join(homeDir, '.config', 'chromium'),
  ].map((item) => path.resolve(item));
  if (dangerous.some((root) => resolved === root || resolved.startsWith(`${root}${path.sep}`))) {
    throw new Error('refusing to use a normal personal browser profile; use a dedicated UEX profile');
  }
  return resolved;
}
