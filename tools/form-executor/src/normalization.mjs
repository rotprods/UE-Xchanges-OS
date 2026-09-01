export function canonicalizeAnswer(fieldType, value) {
  const nfc = (text) => String(text).replace(/\r\n/g, '\n').replace(/\r/g, '\n').normalize('NFC');

  const canonicalDecimal = (input) => {
    if (typeof input === 'boolean') throw new Error('boolean is not a canonical number');
    let raw;
    if (typeof input === 'number') {
      if (!Number.isFinite(input)) throw new Error('number answers must be finite');
      raw = String(input);
    } else if (typeof input === 'string') {
      raw = input.trim();
    } else if (typeof input === 'bigint') {
      raw = input.toString();
    } else {
      throw new Error('number answers must be numeric or decimal string');
    }
    if (!raw) throw new Error('number answer must not be empty');
    const match = raw.match(/^([+-]?)(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/);
    if (!match) throw new Error('number answer is not a valid finite decimal');
    const negative = match[1] === '-';
    const integer = match[2];
    const fraction = match[3] || '';
    const exponent = Number(match[4] || '0') - fraction.length;
    if (!Number.isSafeInteger(exponent)) throw new Error('number exponent is outside canonical range');
    let digits = `${integer}${fraction}`.replace(/^0+/, '');
    if (!digits) return '0';

    let rendered;
    if (exponent >= 0) {
      rendered = digits + '0'.repeat(exponent);
    } else {
      const point = digits.length + exponent;
      if (point <= 0) rendered = `0.${'0'.repeat(-point)}${digits}`;
      else rendered = `${digits.slice(0, point)}.${digits.slice(point)}`;
      rendered = rendered.replace(/0+$/, '').replace(/\.$/, '');
    }
    rendered = rendered.replace(/^0+(?=\d)/, '');
    return negative && rendered !== '0' ? `-${rendered}` : rendered;
  };

  const canonicalDate = (input) => {
    if (typeof input !== 'string') throw new Error('browser date answer must be ISO string');
    const raw = input.trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) throw new Error('date answer must use ISO YYYY-MM-DD');
    const parsed = new Date(`${raw}T00:00:00Z`);
    if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== raw) {
      throw new Error('date answer must be a real ISO calendar date');
    }
    return raw;
  };

  if (value === null || value === undefined) return null;
  if (fieldType === 'text' || fieldType === 'textarea') {
    if (typeof value !== 'string') throw new Error('text-like answers must be strings');
    return nfc(value);
  }
  if (fieldType === 'email') {
    if (typeof value !== 'string') throw new Error('email answers must be strings');
    return nfc(value).trim();
  }
  if (fieldType === 'number') return canonicalDecimal(value);
  if (fieldType === 'date') return canonicalDate(value);
  if (fieldType === 'select' || fieldType === 'radio') {
    if (typeof value !== 'string') throw new Error('choice answers must be strings');
    const normalized = nfc(value).trim();
    if (!normalized) throw new Error('choice answer must be non-empty');
    return normalized;
  }
  if (fieldType === 'checkbox') {
    if (typeof value === 'boolean') return value;
    if (!Array.isArray(value)) throw new Error('checkbox answer must be boolean or array');
    const normalized = value.map((item) => {
      if (typeof item !== 'string') throw new Error('checkbox option answers must be strings');
      const option = nfc(item).trim();
      if (!option) throw new Error('checkbox option answers must be non-empty');
      return option;
    });
    return [...new Set(normalized)].sort();
  }
  if (fieldType === 'consent') {
    if (typeof value !== 'boolean') throw new Error('consent answer must be boolean');
    return value;
  }
  if (fieldType === 'file' || fieldType === 'unknown') {
    throw new Error(`${fieldType} answers are outside canonical model-visible payload identity`);
  }
  throw new Error(`unsupported form field type for canonical normalization: ${fieldType}`);
}
