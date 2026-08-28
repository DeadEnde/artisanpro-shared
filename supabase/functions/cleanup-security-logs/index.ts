// ======================================================================
// cleanup-security-logs — Edge Function (retention job)
//
// Deletes security_logs older than RETENTION_DAYS (default 90). Schedule:
//   supabase functions deploy cleanup-security-logs
//   Then create a Supabase Scheduled job (Dashboard > Database > Cron):
//     select net.http_post(
//       url := '<project>/functions/v1/cleanup-security-logs',
//       headers := '{"Authorization": "Bearer <service-role-key>"}'::jsonb
//     );
// Runs with service role only — never expose to the browser.
// ======================================================================

import { json } from '../_shared/cors.ts';

const RETENTION_DAYS = Number(Deno.env.get('SECURITY_LOG_RETENTION_DAYS') ?? '90');

Deno.serve(async (req: Request) => {
  // Require a shared static secret so only cron/operators can trigger it.
  const expected = Deno.env.get('CRON_SECRET');
  if (!expected || req.headers.get('x-cron-secret') !== expected) {
    return json({ error: 'unauthorized' }, 401);
  }

  const url = Deno.env.get('SUPABASE_URL');
  const serviceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if (!url || !serviceKey) return json({ error: 'misconfigured_runtime' }, 500);

  const cutoff = new Date(Date.now() - RETENTION_DAYS * 24 * 60 * 60 * 1000).toISOString();
  const res = await fetch(
    `${url}/rest/v1/security_logs?created_at=lt.${encodeURIComponent(cutoff)}`,
    {
      method: 'DELETE',
      headers: {
        apikey: serviceKey,
        Authorization: `Bearer ${serviceKey}`,
        Prefer: 'return=representation&count=exact',
      },
    },
  );

  if (!res.ok) return json({ error: 'delete_failed', detail: (await res.text()).slice(0, 200) }, 502);
  const rows = await res.json();
  return json({ ok: true, deleted: Array.isArray(rows) ? rows.length : 0, cutoff });
});
