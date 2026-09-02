import { defaultProfileDir, normalizeAllowedOrigins, normalizeOrigin } from './guard.mjs';

const ALLOWED_CHANNELS = new Set(['chrome', 'chromium', 'msedge']);
const ALLOWED_PROVIDERS = new Set(['generic_html', 'google_forms']);

export function parseInspectArgs(argv, homeDir) {
  const options = {
    url: null,
    profileDir: defaultProfileDir(homeDir),
    allowedOrigins: [],
    headless: false,
    channel: 'chrome',
    timeoutMs: 20_000,
    provider: 'generic_html',
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--headless') {
      options.headless = true;
      continue;
    }
    const valueArgs = new Set(['--url', '--profile-dir', '--allowed-origin', '--channel', '--timeout-ms', '--provider']);
    if (!valueArgs.has(arg)) {
      throw new Error(`unknown inspect-only argument: ${arg}`);
    }
    const value = argv[++i];
    if (!value) throw new Error(`${arg} requires a value`);
    if (arg === '--url') options.url = value;
    else if (arg === '--profile-dir') options.profileDir = value;
    else if (arg === '--allowed-origin') options.allowedOrigins.push(value);
    else if (arg === '--channel') options.channel = value;
    else if (arg === '--timeout-ms') options.timeoutMs = Number(value);
    else if (arg === '--provider') options.provider = value.trim().toLowerCase();
  }

  if (!options.url) throw new Error('--url is required');
  if (!ALLOWED_CHANNELS.has(options.channel)) throw new Error('channel must be chrome, chromium or msedge');
  if (!ALLOWED_PROVIDERS.has(options.provider)) throw new Error('provider is not certified for inspect');
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < 1_000 || options.timeoutMs > 120_000) {
    throw new Error('timeout-ms must be an integer between 1000 and 120000');
  }
  options.allowedOrigins = normalizeAllowedOrigins([normalizeOrigin(options.url), ...options.allowedOrigins]);
  return options;
}
