# ArtisanPro — Plan suivant (approuvé par le propriétaire)

**Date:** 2026-08-29 · **Owner:** ABDELKHALIK Jamily · **Préparé par:** lead-agent
**Contexte:** Phase 1 terminée (29/29 tâches). Page **Réglages** livrée (`aaf7218`).
Ce plan pipelines les propositions de l'agent, classées par valeur/effort.

## Sprint 2 — Product Depth

### 1. devis-branding · P1 (quick win)
**Quoi** — Le devis PDF/preview affiche automatiquement le **nom de l'entreprise, téléphone et ville**
définis dans les Réglages (header + footer). Fallback discret si champs vides.
**Pourquoi** — Confiance instantanée côté client final, exploite la page Réglages fraîchement livrée.

### 2. quotes-pipeline-actions · P1
**Quoi** — Actions par ligne sur la page Devis: brouillon → envoyé → accepté
(persisté local + Supabase), impression/PDF par devis, doublon rapide.
**Dépend** de (1).

### 3. clients-crm-page · P2
**Quoi** — Page **Clients** (lien sidebar) : clients uniques agrégés depuis les devis,
champs téléphone/ville persistés, CA par client, recherche instantanée.
**Dépend** de (2).

### 4. carrelage-module · P1 (gros chantier, 2–3 sessions)
**Quoi** — Activation du module **Carrelage** (actuellement verrouillé) :
moteur (surface, dimensions, marge, cartons de 6, pose), workspace premium
(hints par champ, validation, exports), bibliothèque partagée, tests moteur.
**Dépend** de (3).

### 5. settings-supabase-sync · P2
**Quoi** — Table `user_settings` avec RLS ; les réglages suivent le compte sur tous les
appareils ; `localStorage` reste le fallback hors-ligne.
**Dépend** de (1).

## Règles d'exécution (owner-mandated)
- Après chaque changement : screenshots Playwright **desktop + mobile**, revue visuelle avant push
- Matrice linguistique **FR → EN → AR (RTL)** sur landing/dashboard/modules
- Vérification sur le **deploy Vercel live** après chaque push
- `npm test` 20/20 + `tsc -b && vite build` doivent passer
- `package.json` propre (pas de devDeps de QA committés)
- Wrap-up en fin de session → source ajoutée au **NotebookLM Brain**
