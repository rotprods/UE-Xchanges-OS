import { normalizeAllowedOrigins, normalizeOrigin } from './guard.mjs';

export function humanLoginNavigationDecision({ url, isTopLevelNavigation, allowedOrigins }) {
  if (!isTopLevelNavigation) return { action: 'continue', reason: 'subresource_human_login' };
  let origin;
  try {
    origin = normalizeOrigin(url);
  } catch {
    return { action: 'abort', reason: 'invalid_top_level_url' };
  }
  if (!normalizeAllowedOrigins(allowedOrigins).includes(origin)) {
    return { action: 'abort', reason: 'top_level_origin_not_allowed' };
  }
  return { action: 'continue', reason: 'human_login_allowed_origin' };
}
