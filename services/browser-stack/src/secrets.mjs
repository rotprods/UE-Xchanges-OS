import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export function managedSecretsRoot(homeDir = os.homedir()) {
  return path.resolve(homeDir, '.uexchanges', 'secrets');
}

export function defaultCapabilityKeyPath(homeDir = os.homedir()) {
  return path.join(managedSecretsRoot(homeDir), 'browser-relay-capability.key');
}

export function assertManagedSecretPath(filePath, homeDir = os.homedir()) {
  const root = managedSecretsRoot(homeDir);
  const resolved = path.resolve(filePath);
  if (resolved !== root && !resolved.startsWith(`${root}${path.sep}`)) throw new Error('STACK_SECRET_PATH_OUTSIDE_MANAGED_ROOT');
  return resolved;
}

function assertRegularPrivateFile(filePath) {
  const stat = fs.lstatSync(filePath);
  if (!stat.isFile() || stat.isSymbolicLink()) throw new Error('STACK_SECRET_FILE_TYPE_INVALID');
  if ((stat.mode & 0o077) !== 0) throw new Error('STACK_SECRET_FILE_PERMISSIONS_TOO_OPEN');
}

function parseSecret(raw) {
  const value = raw.trim();
  if (value.length < 32 || /\s/.test(value)) throw new Error('STACK_SECRET_VALUE_INVALID');
  return value;
}

export function loadOrCreateCapabilitySecret({ filePath = defaultCapabilityKeyPath(), homeDir = os.homedir() } = {}) {
  const resolved = assertManagedSecretPath(filePath, homeDir);
  const root = managedSecretsRoot(homeDir);
  fs.mkdirSync(root, { recursive: true, mode: 0o700 });
  const rootStat = fs.lstatSync(root);
  if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) throw new Error('STACK_SECRET_ROOT_INVALID');
  if ((rootStat.mode & 0o077) !== 0) fs.chmodSync(root, 0o700);

  if (!fs.existsSync(resolved)) {
    const secret = crypto.randomBytes(48).toString('base64url');
    const fd = fs.openSync(resolved, fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_WRONLY, 0o600);
    try { fs.writeFileSync(fd, `${secret}\n`, { encoding: 'utf8' }); }
    finally { fs.closeSync(fd); }
    fs.chmodSync(resolved, 0o600);
  }

  assertRegularPrivateFile(resolved);
  const value = parseSecret(fs.readFileSync(resolved, 'utf8'));
  return {
    secret: Buffer.from(value, 'utf8'),
    secretPath: resolved,
    secretRef: `secret:${crypto.createHash('sha256').update(resolved, 'utf8').digest('hex')}`,
  };
}

export function generateEphemeralWorkerToken() {
  return crypto.randomBytes(48).toString('base64url');
}
