# ArtisanPro Shared

Workspace partagé pour le système multi-agent ArtisanPro.

## Structure

```
artisanpro-shared/
├── types/          # Types TypeScript partagés
├── constants/      # Constantes communes
├── supabase/       # Types Supabase & helpers
├── utils/          # Fonctions utilitaires
└── README.md
```

## Usage

Ce module est conçu pour être utilisé comme **git submodule** dans tous les projets ArtisanPro :

- `Artissan-Pro-Admin` — Dashboard admin
- `Artissan-Pro-Client` — App client (futur)
- `Artissan-Pro-API` — API backend (futur)

## Installation

```bash
git submodule add https://github.com/DeadEnde/artisanpro-shared.git artisanpro-shared
```

## Multi-Agent Workspace

Chaque agent IA travaille sur un sous-projet spécifique mais partage les types et constantes via ce module.
