# Workflows Mistral — Nicolas Hespel

Projets de workflows durables déployés en *managed deployment* Mistral Studio
(construction depuis GitHub, aucune brique locale).

## Structure

- `src/workflows/` — définitions des workflows
- `src/entrypoints/worker.py` — worker (découverte + enregistrement)
- `Dockerfile` — image du worker (SDK `mistralai-workflows >= 3.10`)

## Workflows

### revue-mensuelle

Génère la check-list de la revue mensuelle (budget, fraîcheur Knowledge Base,
décisions) au format markdown. Déterministe, sans appel de modèle : coût nul.

Entrée : `{"mois": "AAAA-MM", "remarques": "..."}` (les deux champs facultatifs).

## Déploiement

Le déploiement est géré depuis GitHub (branche `main`, sous-dossier `workflows/`).
Le jeton de compte de service est injecté par la plateforme : aucun secret dans le dépôt.
