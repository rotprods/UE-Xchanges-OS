import test from 'node:test';
import assert from 'node:assert/strict';
import { parseDoctorArgs } from '../src/doctor-args.mjs';


test('doctor defaults to installed Chrome channel', () => {
  assert.deepEqual(parseDoctorArgs([]), { channel: 'chrome' });
});


test('doctor permits only bounded browser channel selection', () => {
  assert.deepEqual(parseDoctorArgs(['--channel', 'chromium']), { channel: 'chromium' });
  assert.deepEqual(parseDoctorArgs(['--channel', 'msedge']), { channel: 'msedge' });
  assert.throws(() => parseDoctorArgs(['--channel', 'firefox']), /channel must be/);
  assert.throws(() => parseDoctorArgs(['--url', 'https://example.org']), /unknown doctor argument/);
  assert.throws(() => parseDoctorArgs(['--submit']), /unknown doctor argument/);
});
