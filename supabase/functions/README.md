# ArtisanPro Edge Functions

Security logging server-side (task `edge-function-security-logs`):
jamais de raw IP / password / token côté navigateur — l'IP est hashée
SHA-256 + sel côté serveur, rétention 90 jours.

## Déploiement (owner, une seule fois)

```bash
npm i -g supabase
supabase login
supabase link --project-ref <PROJECT_REF>

supabase secrets set IP_HASH_SALT=<random-64-chars>
supabase secrets set CRON_SECRET=<random-64-chars>

supabase functions deploy log-security-event
supabase functions deploy cleanup-security-logs
```

## Cron rétention (90 jours)

Dashboard → Database → Cron (pg_cron):

```sql
select cron.schedule(
  'cleanup-security-logs',
  '17 3 * * *',  -- chaque nuit
  $$
  select net.http_post(
    url := 'https://<PROJECT_REF>.supabase.co/functions/v1/cleanup-security-logs',
    headers := jsonb_build_object('x-cron-secret', '<CRON_SECRET>')
  );
  $$
);
```

## Smoke test

```bash
curl -X POST "https://<PROJECT_REF>.supabase.co/functions/v1/log-security-event" \
  -H "apikey: <ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"event":"login_success","email":"demo@artisanpro.ma","meta":{"source":"smoke-test"}}'
# → {"ok":true}   (security_logs reçoit ip_hash, jamais l'IP brute)
```
