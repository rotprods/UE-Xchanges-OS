import { formSchemaFingerprint } from './fingerprint.mjs';
import { validationSignature } from './validation-signature.mjs';

export function buildInspectIdentity({
  provider = 'generic_html',
  canonicalFormUrl,
  structuralFields,
  validationFields,
}) {
  if (typeof provider !== 'string' || !provider.trim()) throw new Error('provider must be non-empty');
  if (typeof canonicalFormUrl !== 'string' || !canonicalFormUrl.trim()) throw new Error('canonicalFormUrl must be non-empty');
  if (!Array.isArray(structuralFields)) throw new Error('structuralFields must be an array');
  if (!Array.isArray(validationFields)) throw new Error('validationFields must be an array');

  return {
    identity_version: '0.1.0',
    provider: provider.trim().toLowerCase(),
    form_fingerprint: formSchemaFingerprint({
      provider,
      canonicalFormUrl,
      fields: structuralFields,
    }),
    validation_signature: validationSignature({
      provider,
      canonicalFormUrl,
      fields: validationFields,
    }),
  };
}
