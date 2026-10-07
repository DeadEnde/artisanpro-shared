#!/usr/bin/env python3
"""
verify-claims.py — ArtisanPro bridge verifier (D20)

Runs concrete, greppable assertions against the real app repo and compares the
result with what bridge/tasks.json claims. This is the anti-drift tool: the
bridge is only as true as the last run of this script.

Usage
-----
    python3 bridge/verify-claims.py --repo ..            # audit only, no writes
    python3 bridge/verify-claims.py --repo .. --write    # audit + rewrite bridge

Exit codes: 0 = bridge matches reality · 1 = drift detected (or --write errors)

Why it exists
-------------
Between 2026-08-29 and 2026-10-07 the bridge claimed work that did not exist in
the code (and marked finished work as todo). Nobody checked. This script makes
that failure mode impossible to repeat silently.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# The verification contract. Each task declares:
#   done_when     -> every assertion must hold for the task to be "done"
#   partial_notes -> free text describing what a partial implementation misses
# A file assertion is (kind, path, regex) with kind in {has, lacks}.
# --------------------------------------------------------------------------
A = lambda path, rx: ("has", path, rx)      # file must match regex
N = lambda path, rx: ("lacks", path, rx)    # file must NOT match regex

CLAIMS = {
    "fix-import-parse": {
        "priority": "P0",
        "done_when": [
            A("src/features/peinture/storage.ts", r"export async function importPaintJson"),
            A("src/features/peinture/storage.ts", r"export async function importPaintCsv"),
            A("src/features/peinture/storage.ts", r"export async function importPaintFile"),
            A("src/features/peinture/PeintureWorkspace.tsx", r"importMessage"),
            A("src/features/peinture/LibraryPanel.tsx", r"onImport"),
        ],
        "evidence": "storage.ts parseur robuste (BOM, ;/,/tab, clés FR/AR, auto-détection) + toast succès/erreur + chargement direct dans le workspace.",
    },
    "devis-branding": {
        "priority": "P1",
        "done_when": [
            A("src/features/peinture/QuotePreview.tsx", r"settings\.companyName"),
            A("src/features/peinture/QuotePreview.tsx", r"settings\.phone"),
            A("src/features/peinture/exporters.ts", r"loadSettings"),
        ],
        "evidence": "QuotePreview en-tête logo+nom+tel+ville depuis les Réglages ; exporters.ts même bloc identité dans les PDF.",
    },
    "signature-canvas": {
        "priority": "P1",
        "done_when": [
            A("src/features/peinture/PeintureWorkspace.tsx", r"toDataURL"),
            A("src/features/peinture/QuotePreview.tsx", r"quoteSignatureZone"),
            A("src/features/peinture/QuotePreview.tsx", r"defaultSignature"),
        ],
        "evidence": "SignatureCanvas souris+tactile -> PNG ; zone « Bon pour accord » par devis + signature par défaut des Réglages.",
    },
    "quotes-pipeline-actions": {
        "priority": "P1",
        "done_when": [
            A("src/main.tsx", r"updateQuoteStatus"),
            A("src/main.tsx", r"duplicateQuote"),
            N("src/main.tsx", r"TODO.*status.*pipeline"),
        ],
        "evidence": "Filtres all/sent/draft/accepted/facture, updateQuoteStatus, duplication, impression et partage WhatsApp.",
    },
    "clients-crm-page": {
        "priority": "P2",
        "done_when": [
            A("src/main.tsx", r"function ClientsPage"),
            A("src/main.tsx", r"clientsMap"),
        ],
        "evidence": "ClientsPage agrège les clients uniques depuis les devis (tél, ville, nb devis, CA), recherche + métriques.",
    },
    "carrelage-module": {
        "priority": "P1",
        "done_when": [
            A("src/features/carrelage/engine.ts", r"export function calculateCarrelage"),
            A("src/features/carrelage/exporters.ts", r"export"),
            A("src/main.tsx", r"/dashboard/carrelage"),
        ],
        "evidence": "Module complet (engine, exporters, library, i18n) + route câblée.",
    },
    "company-logo-branding": {
        "priority": "P1",
        "done_when": [
            A("src/features/settings/SettingsPage.tsx", r"companyLogo"),
            A("src/features/peinture/QuotePreview.tsx", r"companyLogo"),
            A("src/lib/branding.ts", r"const BUCKET = 'branding'"),
            A("src/lib/branding.ts", r"\.upload\("),
            A("src/features/settings/SettingsPage.tsx", r"uploadBranding"),
        ],
        "partial_notes": "Upload + affichage OK, mais le fichier reste en base64 dans localStorage : aucun appel Supabase Storage. Le logo ne suit pas le compte.",
    },
    "profile-edit-avatar-presence": {
        "priority": "P1",
        "done_when": [
            A("src/features/settings/SettingsPage.tsx", r"userAvatar"),
            A("src/lib/sessionPresence.ts", r"heartbeat_session"),
            A("src/context/AppContext.tsx", r"presence"),
            N("src/main.tsx", r'presenceIndicator online"'),
        ],
        "partial_notes": "Édition profil + avatar OK et heartbeat réel, mais le badge de présence est codé en dur (vert permanent) : il ne reflète pas l'état réel de la session.",
    },
    "revenue-progress-widget": {
        "priority": "P2",
        "done_when": [
            A("src/features/analytics/RevenueProgress.tsx", r"role=\"progressbar\""),
            A("src/features/analytics/RevenueProgress.tsx", r"revEmptyTitle"),
            A("src/main.tsx", r"goal=\{settings\.monthlyRevenueGoal"),
        ],
        "partial_notes": "Absent : ClientHome n'affiche que 3 compteurs statiques.",
    },
    "settings-supabase-sync": {
        "priority": "P2",
        "done_when": [
            A("src/features/settings/settingsLib.ts", r"export async function syncSettingsWithRemote"),
            A("src/features/settings/settingsLib.ts", r"export function setSettingsRemoteUser"),
            A("src/context/AppContext.tsx", r"hydrateSettingsFromRemote"),
            A("src/context/AppContext.tsx", r"setSettingsRemoteUser"),
        ],
        "partial_notes": "Fonctions écrites mais jamais appelées : les réglages restent 100% localStorage.",
    },
}

STATUS_DONE = "done"
STATUS_TODO = "todo"


def read(repo, path):
    full = os.path.join(repo, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def run_assertions(repo, assertions):
    """Returns (all_passed, failures, missing_files)."""
    failures, missing = [], []
    for kind, path, rx in assertions:
        content = read(repo, path)
        if content is None:
            failures.append(f"{path}: fichier absent")
            missing.append(path)
            continue
        found = re.search(rx, content) is not None
        if kind == "has" and not found:
            failures.append(f"{path}: attendu /{rx}/ — introuvable")
        elif kind == "lacks" and found:
            failures.append(f"{path}: /{rx}/ ne devrait pas être présent")
    return (not failures), failures, missing


def git_head(repo):
    try:
        return subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="chemin du repo app (ex: ..)")
    ap.add_argument("--write", action="store_true", help="réécrit le bridge")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    bridge_dir = os.path.dirname(os.path.abspath(__file__))
    tasks_path = os.path.join(bridge_dir, "tasks.json")

    if not os.path.isdir(os.path.join(repo, "src")):
        print(f"✗ {repo}/src introuvable — mauvais --repo ?", file=sys.stderr)
        return 1

    head = git_head(repo)
    print(f"━━━ verify-claims · repo {repo} @ {head} ━━━━━━━━━━━━━━━━━━━━━━━━━━")

    results = {}
    for task_id, claim in CLAIMS.items():
        ok, failures, missing = run_assertions(repo, claim["done_when"])
        results[task_id] = {"ok": ok, "failures": failures, "missing": missing}
        mark = "✓ done   " if ok else "✗ incomplet"
        print(f" {mark} {claim['priority']}  {task_id}")
        if not ok:
            for f in failures:
                print(f"              ↳ {f}")

    done = [t for t, r in results.items() if r["ok"]]
    pending = [t for t, r in results.items() if not r["ok"]]
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f" {len(done)} vérifiées faites · {len(pending)} à finir : {', '.join(pending) or '—'}")

    if not args.write:
        print("\n(audit seul — relancer avec --write pour réécrire le bridge)")
        return 0 if not pending else 1

    # ---------------- rewrite bridge ----------------
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    with open(tasks_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    data["version"] = data.get("version", 4) + 1
    data["lastUpdate"] = now
    data["reconciledBy"] = f"verify-claims.py · repo {head}"

    for task in data["tasks"]:
        tid = task["id"]
        if tid not in CLAIMS:
            continue
        r = results[tid]
        task["verifiedAt"] = now
        task["verifiedBy"] = "verify-claims.py (assertions sur le code réel)"
        task["claimedFiles"] = []
        task.pop("claimedAt", None)
        if r["ok"]:
            task["status"] = STATUS_DONE
            task["done"] = [CLAIMS[tid].get("evidence", "vérifié")]
            task["inProgress"] = []
        else:
            task["status"] = STATUS_TODO
            task["done"] = ([CLAIMS[tid]["partial_notes"]] if CLAIMS[tid].get("partial_notes") else [])
            task["next"] = r["failures"] or ["à spécifier"]
            task["assignee"] = ""
            task["inProgress"] = []

    with open(tasks_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    # ---------------- locks: drop stale ones ----------------
    locks_path = os.path.join(bridge_dir, "locks.json")
    with open(locks_path, "r", encoding="utf-8") as fh:
        locks = json.load(fh)
    stale, keep = [], []
    for lock in locks.get("locks", []):
        if not lock.get("agent"):
            stale.append({**lock, "reason": "aucun agent assigné — lock fantôme libéré par verify-claims"})
        else:
            keep.append(lock)
    if stale:
        locks.setdefault("staleLocksReleased", []).extend(stale)
        locks["locks"] = keep
        locks["version"] = locks.get("version", 2) + 1
        locks["lastUpdate"] = now
        with open(locks_path, "w", encoding="utf-8") as fh:
            json.dump(locks, fh, ensure_ascii=False, indent=2)
        print(f" locks.json : {len(stale)} lock(s) fantôme(s) libéré(s)")

    print(" bridge/tasks.json réécrit.")
    return 0 if not pending else 1


if __name__ == "__main__":
    sys.exit(main())
