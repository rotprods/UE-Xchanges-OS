const ALLOWED_CHANNELS = new Set(['chrome', 'chromium', 'msedge']);

export function parseDoctorArgs(argv) {
  const options = { channel: 'chrome' };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg !== '--channel') throw new Error(`unknown doctor argument: ${arg}`);
    const value = argv[++index];
    if (!value) throw new Error('--channel requires a value');
    options.channel = value;
  }
  if (!ALLOWED_CHANNELS.has(options.channel)) throw new Error('channel must be chrome, chromium or msedge');
  return options;
}
