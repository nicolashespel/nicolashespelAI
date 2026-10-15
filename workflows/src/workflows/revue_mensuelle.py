"""Revue mensuelle — génère la check-list de la revue du mois.

Workflow déterministe, sans appel de modèle (coût nul).
Règles de la revue : sujet Knowledge « Journal des revues » de Nicolas.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field

import mistralai.workflows as workflows


class RevueInput(BaseModel):
    """Entrée de la revue mensuelle."""

    mois: str = Field(
        default="",
        description="Mois de la revue au format AAAA-MM. Vide = mois en cours.",
    )
    remarques: str = Field(
        default="",
        description="Remarques à intégrer dans la revue (facultatif).",
    )


@workflows.activity()
async def generer_checklist(mois: str, remarques: str) -> str:
    """Construit la check-list de la revue au format markdown."""
    maintenant = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    mois_effectif = mois or datetime.now(timezone.utc).strftime("%Y-%m")
    lignes = [
        f"# Revue mensuelle — {mois_effectif}",
        "",
        f"Générée le {maintenant} par le workflow revue-mensuelle (zéro appel de modèle).",
        "",
        "## 1. Budget",
        "- Crédit offert du mois : 8,50 EUR (API et Vibe Code).",
        "- Plafond : stop après 10 EUR de crédit payé consommé au-delà du crédit offert.",
        "- Usage projeté : ~20 EUR/mois, soit ~11,50 EUR payés — vigilance sur le léger dépassement.",
        "- Décision à consigner : conserver le pay-as-you-go ou ajuster le plafond.",
        "",
        "## 2. Fraîcheur de la Knowledge Base",
        "- Documents ajoutés / supprimés / corrigés ce mois-ci ?",
        "- Corrections validées ou refusées à consigner dans le journal des revues.",
        "",
        "## 3. Décisions",
        "- Consigner chaque décision (outils, budget, sources) avec sa date.",
        "- Rien enregistrer depuis une source connectée sans accord explicite.",
        "",
        "## 4. Remarques",
    ]
    remarques_texte = remarques.strip() if remarques and remarques.strip() else "- (aucune)"
    lignes.append(remarques_texte)
    return chr(10).join(lignes)


@workflows.workflow.define(
    name="revue-mensuelle",
    workflow_display_name="Revue mensuelle",
    workflow_description="Génère la check-list de la revue mensuelle (budget, KB, décisions) sans appel de modèle.",
)
class RevueMensuelleWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: RevueInput) -> str:
        return await generer_checklist(mois=input.mois, remarques=input.remarques)
