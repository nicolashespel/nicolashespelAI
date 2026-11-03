"""Workflow de validation de requêtes SEO — blog Build Digital & AUTAGE (projet 5).

Spécification validée par Nicolas le 01/11/2026 :
- 3 appels Serper.dev par requête : guillemets, allintitle, requête simple ;
- seuils : guillemets < 2000, allintitle < 50, KGR < 0,25 (pépite) ;
- vérification d'intention : domaines des 5 premiers résultats ;
- verdict : Go / Écart / À vérifier, avec motif chiffré.

La clé API Serper est lue depuis la variable d'environnement SERPER_API_KEY,
liée à un secret du workspace Mistral — jamais en clair dans le dépôt.
"""

import os
from typing import Optional

import httpx
from pydantic import BaseModel, Field

import mistralai.workflows as workflows

SERPER_ENDPOINT = "https://google.serper.dev/search"
NOMBRE_RESULTATS_INTENTION = 5
SEUIL_GUILLEMETS = 2_000
SEUIL_ALLINTITLE = 50
SEUIL_KGR = 0.25


class Requete(BaseModel):
    """Une requête à valider."""

    identifiant: str = Field(description="Identifiant court, ex. BD3 ou N6")
    societe: str = Field(description="Build Digital ou AUTAGE")
    requete: str = Field(description="Formulation exacte de la requête")
    volume_mensuel: Optional[int] = Field(
        default=None, description="Volume de recherche mensuel (Ubersuggest), optionnel"
    )


class ValidationEntree(BaseModel):
    """Entrée du workflow : la liste des requêtes à valider."""

    requetes: list[Requete]


class ResultatRequete(BaseModel):
    """Résultat complet d'une requête."""

    identifiant: str
    societe: str
    requete: str
    volume_mensuel: Optional[int] = None
    guillemets: Optional[int] = None
    allintitle: Optional[int] = None
    kgr: Optional[float] = None
    intention_top: list[str] = Field(default_factory=list)
    verdict: str = ""
    motif: str = ""


class ValidationSortie(BaseModel):
    """Sortie du workflow : un résultat par requête."""

    resultats: list[ResultatRequete] = Field(default_factory=list)


async def _appel_serper(requete: str) -> dict:
    """Un appel POST à l'API Serper (France, français)."""
    cle = os.environ.get("SERPER_API_KEY", "")
    if not cle:
        raise RuntimeError(
            "SERPER_API_KEY absente : lier le secret du workspace au déploiement."
        )
    async with httpx.AsyncClient(timeout=30.0) as client:
        reponse = await client.post(
            SERPER_ENDPOINT,
            headers={"X-API-KEY": cle, "Content-Type": "application/json"},
            json={"q": requete, "hl": "fr", "gl": "fr", "num": 10},
        )
        reponse.raise_for_status()
        return reponse.json()


def _compteur_total(donnees: dict) -> Optional[int]:
    """Extrait le nombre total de résultats annoncé par Google, si présent."""
    valeur = donnees.get("totalResults")
    if isinstance(valeur, int):
        return valeur
    info = donnees.get("searchInformation")
    if isinstance(info, dict):
        valeur = info.get("totalResults")
        if isinstance(valeur, int):
            return valeur
    return None


@workflows.activity()
async def compter_guillemets(requete: str) -> Optional[int]:
    """Nombre de résultats Google pour la requête entre guillemets."""
    return _compteur_total(await _appel_serper('“' + requete + '”'))


@workflows.activity()
async def compter_allintitle(requete: str) -> Optional[int]:
    """Nombre de résultats Google pour allintitle:requete."""
    return _compteur_total(await _appel_serper("allintitle:" + requete))


@workflows.activity()
async def sommaire_intention(requete: str) -> list[str]:
    """Domaine et titre des premiers résultats de la requête simple."""
    donnees = await _appel_serper(requete)
    sommaire: list[str] = []
    for resultat in donnees.get("organic", [])[:NOMBRE_RESULTATS_INTENTION]:
        lien = str(resultat.get("link") or "")
        domaine = lien.split("/")[2] if "://" in lien else lien
        titre = str(resultat.get("title") or "")[:70]
        sommaire.append(domaine + " — " + titre)
    return sommaire


def _verdict(
    guillemets: Optional[int], allintitle: Optional[int], volume: Optional[int]
) -> tuple[str, str]:
    """Applique les seuils validés et renvoie (verdict, motif)."""
    if guillemets is None or allintitle is None:
        return (
            "À vérifier",
            "Compteur Google indisponible via Serper — vérification manuelle requise",
        )
    if guillemets >= SEUIL_GUILLEMETS:
        return "Écart", "Guillemets " + str(guillemets) + " >= " + str(SEUIL_GUILLEMETS)
    if allintitle >= SEUIL_ALLINTITLE:
        return "Écart", "Allintitle " + str(allintitle) + " >= " + str(SEUIL_ALLINTITLE)
    motif = (
        "Guillemets " + str(guillemets) + " < " + str(SEUIL_GUILLEMETS)
        + " ; allintitle " + str(allintitle) + " < " + str(SEUIL_ALLINTITLE)
    )
    return "Go", motif


@workflows.workflow.define(
    name="validation-requetes-seo",
    workflow_display_name="Validation de requêtes SEO",
    workflow_description=(
        "Valide des requêtes de blog : compteurs Google (guillemets, allintitle), "
        "KGR et intention via Serper.dev — seuils < 2000 / < 50 / < 0,25."
    ),
)
class ValidationRequetesSeo:
    @workflows.workflow.entrypoint
    async def run(self, entree: ValidationEntree) -> ValidationSortie:
        resultats: list[ResultatRequete] = []
        for requete in entree.requetes:
            guillemets = await compter_guillemets(requete.requete)
            allintitle = await compter_allintitle(requete.requete)
            intention = await sommaire_intention(requete.requete)
            kgr: Optional[float] = None
            if allintitle is not None and requete.volume_mensuel:
                kgr = round(allintitle / requete.volume_mensuel, 2)
            verdict, motif = _verdict(guillemets, allintitle, requete.volume_mensuel)
            if verdict == "Go" and kgr is not None:
                if kgr < SEUIL_KGR:
                    verdict = "Go — pépite"
                motif = motif + " ; KGR " + str(kgr)
            resultats.append(
                ResultatRequete(
                    identifiant=requete.identifiant,
                    societe=requete.societe,
                    requete=requete.requete,
                    volume_mensuel=requete.volume_mensuel,
                    guillemets=guillemets,
                    allintitle=allintitle,
                    kgr=kgr,
                    intention_top=intention,
                    verdict=verdict,
                    motif=motif,
                )
            )
        return ValidationSortie(resultats=resultats)
