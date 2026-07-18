"""Triplets ESMM : extraction stricte depuis les réponses des modèles.

Cause racine n°2 du « 0 triplet » historique (audit `lyra_clean_bis`) : la
résolution d'entités importait une fonction inexistante, l'ImportError était
avalé, chaque triplet était silencieusement ignoré. Ici :
- extraction = parsing JSON STRICT (`json.loads`, jamais d'`eval` — charte §6) ;
- les échecs de parsing sont COMPTÉS et retournés, jamais avalés (charte §2) ;
- la résolution d'entités v1 est une normalisation pure (aucun import fragile,
  pas d'embeddings — ils viendront avec leur calibration, pas avant).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import hashlib
import json
import re


_ARTICLE_RE = re.compile(r"^(?:le |la |les |l'|l’|un |une |des |du |de la |de |d'|d’|the |a |an )+", re.I)


def normalize_entity(s: str) -> str:
    """Résolution d'entités v1 : minuscules, espaces normalisés, ponctuation de
    bord, articles de tête retirés (« l'auto-similarité » ≡ « auto-similarité »)."""
    s = re.sub(r"\s+", " ", (s or "").strip().lower())
    s = _ARTICLE_RE.sub("", s)
    return s.strip(".,;:!?\"'()[]{} ")


def match_key(s: str) -> str:
    """Clé d'égalité lexicale STRICTE pour le consensus : normalisation + fusion
    des tirets/espaces (« auto-similarité » ≡ « autosimilarité » — cas observé en
    live à cosinus 0.744, sous le seuil sémantique) + PLIAGE DES DIACRITIQUES
    (« géométrie » ≡ « geometrie » : les modèles sont incohérents sur les accents,
    et Jaro-Winkler à 0.9 ne les rattrape pas — mesuré à 0.877)."""
    import unicodedata
    s = normalize_entity(s).replace("-", "").replace(" ", "")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


@dataclass(frozen=True)
class Triplet:
    subject: str
    predicate: str
    object: str

    def signature(self) -> str:
        """Signature SHA256 du triplet normalisé (design consensus de l'audit)."""
        canon = "|".join(normalize_entity(x) for x in (self.subject, self.predicate, self.object))
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def pair_signature(self) -> str:
        """Signature de la PAIRE (sujet, objet) — consensus de niveau 2 : deux
        modèles qui nomment le même lien avec des prédicats différents valident
        la même connaissance (constat live 2026-07-18 : l'accord exact entre
        modèles hétérogènes est quasi inatteignable)."""
        canon = "|".join(normalize_entity(x) for x in (self.subject, self.object))
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def is_valid(self) -> bool:
        return all(normalize_entity(x) for x in (self.subject, self.predicate, self.object))


@dataclass
class Extraction:
    """Résultat d'extraction pour UN modèle : triplets valides + erreurs comptées."""
    model: str
    triplets: List[Triplet] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


_JSON_RE = re.compile(r"\{.*\}", re.S)


def extract_triplets(model: str, text: str) -> Extraction:
    """Extrait les triplets d'UNE réponse d'UN modèle (jamais de concaténation

    inter-modèles — cause racine n°3 exclue par construction : le consensus
    reçoit des extractions séparées par modèle).
    Format attendu : {"triplets": [{"sujet": ..., "predicat": ..., "objet": ...}]}
    (clés anglaises subject/predicate/object acceptées aussi).
    """
    ext = Extraction(model=model)
    if not text or not text.strip():
        ext.errors.append("réponse vide")
        return ext
    m = _JSON_RE.search(text)
    if not m:
        ext.errors.append("aucun JSON dans la réponse")
        return ext
    try:
        payload = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        ext.errors.append(f"JSON invalide : {e}")
        return ext
    raw = payload.get("triplets")
    if not isinstance(raw, list):
        ext.errors.append("clé 'triplets' absente ou non-liste")
        return ext
    for i, t in enumerate(raw):
        if not isinstance(t, dict):
            ext.errors.append(f"triplet {i} non-dict")
            continue
        trip = Triplet(
            subject=str(t.get("sujet", t.get("subject", ""))),
            # « prédicat » accentué : constaté en live chez gemma3 (15 rejets)
            predicate=str(t.get("predicat", t.get("prédicat", t.get("predicate", "")))),
            object=str(t.get("objet", t.get("object", ""))),
        )
        if trip.is_valid():
            ext.triplets.append(trip)
        else:
            ext.errors.append(f"triplet {i} incomplet : {t}")
    return ext
