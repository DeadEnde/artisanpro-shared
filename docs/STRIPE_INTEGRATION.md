# ArtisanPro — Architecture Intégration Stripe

Préparation Stripe & Facturation (tasks `manual-payments-stripe-prep` & `admin-billing-payments`).

## 1. Workflow Hybride (Manuel + Stripe)

1. **Paiement Manuel (Virement, Espèces, Chèque)**:
   - Administrateur saisit le règlement dans l'Admin `SubscriptionPanel`
   - Sélection du mode de règlement + référence de transaction (ex: `VIR-2026-089`)
   - Présélections rapides de renouvellement (+30j, +90j, +365j)
   - Exécution du RPC `admin_set_subscription_status` qui débloque les modules en temps réel

2. **Paiement Stripe (SaaS automatisé)**:
   - Client initie le checkout Stripe avec `client_reference_id = user.id`
   - Stripe envoie les événements webhook à l'Edge Function `/functions/v1/stripe-webhook`
   - Vérification cryptographique HMAC-SHA256 de la signature Stripe (`stripe-signature`)
   - Événements gérés :
     * `checkout.session.completed` : Active l'abonnement pour 30 jours
     * `customer.subscription.deleted` : Marque l'abonnement comme annulé / expiré

## 2. Déploiement Webhook

```bash
supabase secrets set STRIPE_SECRET_KEY=sk_live_...
supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_...
supabase functions deploy stripe-webhook
```

URL de webhook à configurer dans le Dashboard Stripe :
`https://<PROJECT_REF>.supabase.co/functions/v1/stripe-webhook`
