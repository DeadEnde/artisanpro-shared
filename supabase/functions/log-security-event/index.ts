// ======================================================================
// log-security-event — Edge Function (security-agent, task edge-function-security-logs)
//
// Server-side security logging. The browser sends ONLY the event payload;
// the IP is extracted from proxy headers and stored exclusively as a
// salted SHA-256 hash. Raw IPs, passwords, tokens and service keys never
// reach the client, the logs, or the database.
//
// Env (provided by Supabase, no secrets in the repo):
//   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY  — auto-injected by the runtime
//   IP_HASH_SALT                             — set via: supabase secrets set IP_HASH_SALT=...
// ======================================================================

import { preflight, json } from '../_shared/cors.ts';

const ALLOWED_EVENTS = new Set([
  'login_success', 'login_failed', 'access_denied', 'account_blocked',
  'logout', 'forced_logout', 'session_started', 'session_expired',
]);

const textEncoder = new TextEncoder();

async function sha256hex(input: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', textEncoder.encode(input));
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

function clientIp(req: Request): string | null {
  const fwd = req.headers.get('x-forwarded-for');
  if (fwd) return fwd.split(',')[0].trim();
  return req.headers.get('x-real-ip');
}

Deno.serve(async (req: Request) => {
  const pre = preflight(req);
  if (pre) return pre;
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: 'invalid_json' }, 400);
  }

  const event = String(body.event ?? '');
  if (!ALLOWED_EVENTS.has(event)) return json({ error: 'unknown_event' }, 400);

  // Whitelisted payload only — anything else is dropped silently.
  const userId = typeof body.user_id === 'string' ? body.user_id : null;
  const email = typeof body.email === 'string' ? body.email.slice(0, 254) : null;
  const meta = body.meta && typeof body.meta === 'object' && !Array.isArray(body.meta)
    ? Object.fromEntries(
        Object.entries(body.meta as Record<string, unknown>)
          .filter(([, v]) => ['string', 'number', 'boolean'].includes(typeof v))
          .slice(0, 12),
      )
    : {};

  const salt = Deno.env.get('IP_HASH_SALT') ?? 'artisanpro-default-salt';
  const ip = clientIp(req);
  const ipHash = ip ? await sha256hex(`${salt}:${ip}`) : null;
  const userAgent = (req.headers.get('user-agent') ?? '').slice(0, 512) || null;

  const url = Deno.env.get('SUPABASE_URL');
  const serviceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if (!url || !serviceKey) return json({ error: 'misconfigured_runtime' }, 500);

  const res = await fetch(`${url}/rest/v1/security_logs`, {
    method: 'POST',
    headers: {
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
      'Content-Type': 'application/json',
      Prefer: 'return=minimal',
    },
    body: JSON.stringify({
      event,
      user_id: userId,
      email,
      ip_hash: ipHash,
      user_agent: userAgent,
      metadata: meta,
    }),
  });

  if (!res.ok) {
    const detail = await res.text();
    return json({ error: 'insert_failed', detail: detail.slice(0, 200) }, 502);
  }
  return json({ ok: true });
});
