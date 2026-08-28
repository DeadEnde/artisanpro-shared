// ======================================================================
// stripe-webhook — Edge Function (billing-agent, task manual-payments-stripe-prep)
//
// Handles Stripe subscription webhooks (checkout.session.completed,
// customer.subscription.updated/deleted, invoice.payment_succeeded).
// Automatically activates or expires user subscription entitlements in Supabase.
//
// Env:
//   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY  — auto-injected by Supabase
//   STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET  — set via supabase secrets set
// ======================================================================

import { preflight, json } from '../_shared/cors.ts';

const textEncoder = new TextEncoder();

async function verifyStripeSignature(payload: string, header: string, secret: string): Promise<boolean> {
  const parts = Object.fromEntries(header.split(',').map((p) => p.trim().split('=')));
  const timestamp = parts.t;
  const signature = parts.v1;
  if (!timestamp || !signature) return false;

  const key = await crypto.subtle.importKey(
    'raw',
    textEncoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const signedPayload = `${timestamp}.${payload}`;
  const hmac = await crypto.subtle.sign('HMAC', key, textEncoder.encode(signedPayload));
  const expectedSig = Array.from(new Uint8Array(hmac)).map((b) => b.toString(16).padStart(2, '0')).join('');
  return expectedSig === signature;
}

Deno.serve(async (req: Request) => {
  const pre = preflight(req);
  if (pre) return pre;
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);

  const rawBody = await req.text();
  const stripeSig = req.headers.get('stripe-signature') || '';
  const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET');

  // Verify signature if secret is configured
  if (webhookSecret) {
    const isValid = await verifyStripeSignature(rawBody, stripeSig, webhookSecret);
    if (!isValid) return json({ error: 'invalid_signature' }, 400);
  }

  let event: Record<string, any>;
  try {
    event = JSON.parse(rawBody);
  } catch {
    return json({ error: 'invalid_json' }, 400);
  }

  const url = Deno.env.get('SUPABASE_URL');
  const serviceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if (!url || !serviceKey) return json({ error: 'misconfigured_runtime' }, 500);

  const eventType = String(event.type || '');
  const dataObject = event.data?.object || {};

  switch (eventType) {
    case 'checkout.session.completed': {
      const userId = dataObject.client_reference_id || dataObject.metadata?.user_id;
      const planName = dataObject.metadata?.plan_name || 'Peinture Pro';
      const amount = (dataObject.amount_total || 9900) / 100;
      if (userId) {
        const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
        await fetch(`${url}/rest/v1/rpc/admin_set_subscription_status`, {
          method: 'POST',
          headers: { apikey: serviceKey, Authorization: `Bearer ${serviceKey}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ p_user_id: userId, p_plan_name: planName, p_status: 'active', p_expires_at: expiresAt, p_amount: amount }),
        });
      }
      break;
    }
    case 'customer.subscription.deleted': {
      const userId = dataObject.metadata?.user_id;
      if (userId) {
        await fetch(`${url}/rest/v1/rpc/admin_set_subscription_status`, {
          method: 'POST',
          headers: { apikey: serviceKey, Authorization: `Bearer ${serviceKey}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ p_user_id: userId, p_plan_name: dataObject.metadata?.plan_name || 'Peinture Pro', p_status: 'cancelled', p_expires_at: null, p_amount: 0 }),
        });
      }
      break;
    }
    default:
      break;
  }

  return json({ received: true, event: eventType });
});
