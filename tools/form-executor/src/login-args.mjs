import { defaultProfileDir, normalizeAllowedOrigins, normalizeOrigin } from './guard.mjs';

const ALLOWED_CHANNELS = new Set(['chrome', 'chromium', 'msedge']);

function assertNonSecretInitialUrl(value) {
  const parsed = new URL(value);
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('login URL must use http or https');
  if (parsed.username || parsed.password) throw new Error('login URL must not contain embedded credentials');
  if (parsed.search || parsed.hash) {
    throw new Error('initial login URL must not contain query or fragment material; use a provider base login URL');
  }
  return parsed.href;
}

export function parseHumanLoginArgs(argv, homeDir) {
  const options = {
    url: null,
    profileDir: defaultProfileDir(homeDir),
    allowedOrigins: [],
    channel: 'chrome',
    timeoutMs: 20_000,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const valueArgs = new Set(['--url', '--profile-dir', '--allowed-origin', '--channel', '--timeout-ms']);
    if (!valueArgs.has(arg)) throw new Error(`unknown human-login argument: ${arg}`);
    const value = argv[++index];
    if (!value) throw new Error(`${arg} requires a value`);
    if (arg === '--url') options.url = assertNonSecretInitialUrl(value);
    else if (arg === '--profile-dir') options.profileDir = value;
    else if (arg === '--allowed-origin') options.allowedOrigins.push(value);
    else if (arg === '--channel') options.channel = value;
    else if (arg === '--timeout-ms') options.timeoutMs = Number(value);
  }

  if (!options.url) throw new Error('--url is required');
  if (!ALLOWED_CHANNELS.has(options.channel)) throw new Error('channel must be chrome, chromium or msedge');
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < 1_000 || options.timeoutMs > 120_000) {
    throw new Error('timeout-ms must be an integer between 1000 and 120000');
  }
  options.allowedOrigins = normalizeAllowedOrigins([normalizeOrigin(options.url), ...options.allowedOrigins]);
  return options;
}
