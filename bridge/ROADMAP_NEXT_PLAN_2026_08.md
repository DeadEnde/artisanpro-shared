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

---

## Amendement 2026-08-29 (owner feedback — 5 nouvelles tâches)

### 0. fix-import-parse · P0 🔴 (priorité absolue)
Bug terrain: l'import JSON/CSV **ne charge rien**. Parser robuste (BOM, guillemets,
virgules, valeurs FR/AR), auto-détection, toast succès/erreur, chargement des
données du fichier dans le calculateur + bibliothèque.

### 2b. company-logo-branding · P1
Upload du **logo d'entreprise** dans les Réglages (local + Supabase Storage),
affiché sur l'en-tête de la facture/devis et dans les exports.

### 2c. signature-canvas · P1
**Signature dessinée à l'écran** (doigt/souris) sauvegardée par devis et
imprimée dans la zone "bon pour accord" + exports.

### 3b. profile-edit-avatar-presence · P1
Réglages: édition des informations, **photo de profil** (avatar dans sidebar/topbar),
badge de **présence en ligne** (vert si heartbeat actif, gris sinon).

### 4b. revenue-progress-widget · P2
Widget dashboard: **CA du mois** en temps réel, courbe 6 mois, barre de
progression vers un objectif mensuel éditable.

**Ordre d'exécution actualisé:**
fix-import-parse → devis-branding → company-logo-branding → signature-canvas →
quotes-pipeline-actions → clients-crm-page → profile-edit-avatar-presence →
revenue-progress-widget → carrelage-module → settings-supabase-sync
