import axios from 'axios';

const AI_TRACK_URL = 'http://localhost:8000/api/ai/track';
const AI_KB_BUILD_URL = 'http://localhost:8008/api/ai/kb/build';
const ANALYTICS_BASE = 'http://localhost:8000/api/analytics';

/**
 * Returns the AI user ID — prefers the real auth user ID,
 * falls back to a stable anonymous localStorage ID.
 */
export function getAIUserId(authUser) {
  if (authUser?.id) {
    localStorage.setItem('ai_user_id', authUser.id);
    return String(authUser.id);
  }
  const k = 'ai_user_id';
  const stored = localStorage.getItem(k);
  if (stored) return stored;
  const id = 'u_' + Math.random().toString(36).slice(2, 12);
  localStorage.setItem(k, id);
  return id;
}

/**
 * Returns common headers to include on product-service API calls
 * so the server can auto-track behavior with the correct user ID.
 */
export function behaviorHeaders(userId) {
  return userId ? { 'X-User-ID': String(userId) } : {};
}

/**
 * Fire-and-forget behavior track to AI service (Redis) + product-service analytics DB.
 * The ai-service /track endpoint internally persists to DB as a background task.
 */
export function trackBehavior(userId, productId, eventType = 'view_detail') {
  if (!userId || !productId) return;
  axios.post(AI_TRACK_URL, {
    user_id: String(userId),
    product_id: String(productId),
    event_type: eventType,
  }).catch(() => {});
}

/**
 * Track a search query directly to product-service analytics.
 * Use this alongside the search API call.
 */
export function trackSearch(userId, query, resultsCount = 0) {
  if (!userId || !query) return;
  axios.post(`${ANALYTICS_BASE}/search/`, {
    user_id: String(userId),
    session_id: 'frontend',
    query: String(query).slice(0, 255),
    results_count: resultsCount,
  }).catch(() => {});
}

export async function forceRebuildKB() {
  try {
    await axios.post(AI_KB_BUILD_URL);
    return true;
  } catch (_) {
    return false;
  }
}
