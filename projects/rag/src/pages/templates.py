"""
Templates de pages pour le système RAG Wiki.

Ce module contient la classe PageTemplates qui fournit les templates
pour les différentes pages du vault.
"""


class PageTemplates:
    """
    Templates de pages pour le système RAG Wiki.
    
    Cette classe fournit les templates de base pour les différentes
    pages du vault.
    """
    
    def get_entity_template(self) -> str:
        """
        Obtenir le template pour une page d'entité.
        
        Returns:
            Template markdown.
        """
        return """# {{name}}

## Description
{{description}}

## Contexte
[Contexte historique et importance]

## Relations
[Liste des relations avec d'autres entités et concepts]

## Contributions/Activités
[Liste des contributions ou activités]

## Références
{%- if related %}
{%- for item in related %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
{%- if sources %}
{%- for item in sources %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
"""
    
    def get_concept_template(self) -> str:
        """
        Obtenir le template pour une page de concept.
        
        Returns:
            Template markdown.
        """
        return """# {{name}}

## Définition
{{description}}

## Contexte
[Contexte historique et développement]

## Fonctionnement
[Explication du fonctionnement interne]

### Architecture
[Description de l'architecture]

### Mécanismes
[Explication des mécanismes]

## Applications
[Liste des applications]

## Avantages
[Liste des avantages]

## Limites
[Liste des limites]

## Variantes
[Liste des variantes]

## Références
{%- if related %}
{%- for item in related %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
{%- if sources %}
{%- for item in sources %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
"""
    
    def get_source_template(self) -> str:
        """
        Obtenir le template pour une page de source.
        
        Returns:
            Template markdown.
        """
        return """# {{title}}

## Métadonnées
- **Auteurs :** {{authors}}
- **Date :** {{date}}
- **Type :** {{source_type}}
{%- if url %}
- **URL :** [{{url}}]({{url}})
{%- endif %}
{%- if doi %}
- **DOI :** {{doi}}
{%- endif %}

## Résumé
{{summary}}

## Points clés
[Liste des points clés extraits]

## Citations
[Extraits importants avec citations de page/section]

## Analyse
[Analyse et interprétation par le LLM]

## Connexions
[Liste des connexions avec d'autres pages]

## Notes
[Notes supplémentaires et réflexions]

## Références
{%- if related %}
{%- for item in related %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
"""
    
    def get_comparison_template(self) -> str:
        """
        Obtenir le template pour une page de comparaison.
        
        Returns:
            Template markdown.
        """
        return """# {{name}}

## Introduction
[Introduction au sujet de la comparaison]

## Critères de comparaison

{%- for criterion in criteria %}
### {{criterion}}
[Analyse détaillée pour ce critère]

{%- endfor %}

## Avantages et inconvénients

{%- for subject in subjects %}
### {{subject}}
**Avantages:**
- [Liste des avantages]

**Inconvénients:**
- [Liste des inconvénients]

{%- endfor %}

## Conclusion
[Conclusion et recommandations]

## Références
{%- if related %}
{%- for item in related %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
{%- if sources %}
{%- for item in sources %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
"""
    
    def get_synthesis_template(self) -> str:
        """
        Obtenir le template pour une page de synthèse.
        
        Returns:
            Template markdown.
        """
        return """# {{name}}

## Executive Summary
{{description}}

## Contexte
[Contexte et importance du sujet]

## État de l'art
[Vue d'ensemble de l'état actuel]

### Approches principales
[Liste des approches principales]

### Défis actuels
[Liste des défis]

## Tendances
[Analyse des tendances]

## Prédictions
[Prédictions pour l'avenir]

## Recommandations
[Recommandations stratégiques]

## Références
{%- if related %}
{%- for item in related %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
{%- if sources %}
{%- for item in sources %}
- [[{{item}}]]
{%- endfor %}
{%- endif %}
"""
    
    def get_index_template(self) -> str:
        """
        Obtenir le template pour une page d'index.
        
        Returns:
            Template markdown.
        """
        return """# {{name}}

## Statistiques
- **Total pages :** {{statistics.total_pages}}
- **Entités :** {{statistics.entities}}
- **Concepts :** {{statistics.concepts}}
- **Sources :** {{statistics.sources}}
- **Comparaisons :** {{statistics.comparisons}}
- **Synthèses :** {{statistics.syntheses}}
- **Dernière mise à jour :** {{generated}}

## Par Type

{%- for type, pages in pages_by_type.items() %}
### {{type.capitalize()}} ({{pages|length}})
{%- for page in pages %}
- [[{{page}}]]
{%- endfor %}

{%- endfor %}

## Par Tag

{%- for tag, pages in pages_by_tag.items() %}
### {{tag}} ({{pages|length}})
{%- for page in pages %}
- [[{{page}}]]
{%- endfor %}

{%- endfor %}

## Par Date

{%- for date, pages in pages_by_date.items() %}
### {{date}} ({{pages|length}})
{%- for page in pages %}
- [[{{page}}]]
{%- endfor %}

{%- endfor %}

## Recherche
Utilisez les commandes `/wiki-query` ou `/wiki-search` pour trouver du contenu.
"""
    
    def get_log_template(self) -> str:
        """
        Obtenir le template pour une page de log.
        
        Returns:
            Template markdown.
        """
        return """# {{name}}

{{description}}

{%- for entry in entries %}
## {{entry.timestamp[:10]}}

### {{entry.timestamp[11:19]}} - {{entry.operation}}
- **Durée :** {{entry.duration_seconds}}s
- **Status :** {'✅' if entry.success else '❌'}
{%- if entry.details %}
{%- for key, value in entry.details.items() %}
- **{{key}}:** {{value}}
{%- endfor %}
{%- endif %}

{%- endfor %}
"""
