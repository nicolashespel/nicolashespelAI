# Validation de requêtes SEO

Workflow Mistral du projet 5 (blog Build Digital & AUTAGE) : valide les requêtes de blog via l'API Serper.dev.

Pour chaque requête : compteurs Google (guillemets < 2 000, allintitle < 50), KGR < 0,25 (pépite) et les 5 premiers domaines des résultats (vérification d'intention). Verdict : Go / Écart / À vérifier, avec motif chiffré.

## Déploiement géré Mistral

- Répertoire de build : `workflows/validation-requetes-seo`
- Secret requis : `SERPER_API_KEY` (Secrets Manager du workspace, lié à la variable d'environnement du même nom — jamais en clair dans le dépôt)
- Exécution : workflow `validation-requetes-seo`, entrée :

```json
{"requetes": [
  {"identifiant": "BD3", "societe": "Build Digital", "requete": "pourquoi mon entreprise n'apparaît pas sur Google", "volume_mensuel": 71}
]}
```
