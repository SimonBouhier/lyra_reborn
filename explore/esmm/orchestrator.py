"""Orchestrateur ESMM : lacune → exploration multi-modèles → consensus → graphe.

Ré-implémentation du design de `lyra_clean_bis/services/esmm` (la pépite n°1 du
lot 1) avec les trois causes racines du « 0 triplet » structurellement exclues :
1. **Amorçage obligatoire** : l'orchestrateur REFUSE de tourner sur un graphe
   vide sans graines (l'original lançait ses cycles sur des littéraux de
   secours, en silence).
2. **Extraction sans piège** : parsing JSON strict, erreurs comptées
   (triplets.py) — pas de résolution d'entités importée à l'aveugle.
3. **Consensus par-modèle** : structurellement garanti (consensus.py).

Charte §1 (anti « vert mais vide ») : `run()` lève `EsmmEmptyRun` si, après tous
les cycles, AUCUN triplet n'a été accepté — l'échec est bruyant, jamais un
rapport vert sur du vide. (L'original : 71 cycles « réussis », 0 triplet.)

La « cochaîne » épistémique (design 5D de l'audit, v1 honnête) : chaque concept
porte dans `node.data["cochain"]` un enregistrement {support, diversity,
sources, updated_cycle} — la matière des futures signatures.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from memory.graph.store import GraphStore
from explore.esmm.triplets import Extraction, extract_triplets, normalize_entity
from explore.esmm.gaps import Gap, GapDetector
from explore.esmm.consensus import vote, ConsensusResult


class EsmmEmptyRun(RuntimeError):
    """Un run qui ne produit rien N'EST PAS un succès silencieux."""


PREDICATE_VOCAB = ("est_un", "partie_de", "propriete_de", "cause", "utilise",
                   "exemple_de", "oppose_a", "lie_a")

EXPLORE_PROMPT = """Tu es un explorateur de connaissances. Concept à explorer : « {concept} »
(lacune détectée : {gap_type} — {detail}).

Propose 3 à 6 relations factuelles autour de ce concept.
Contraintes STRICTES (constat : sans elles, aucun accord inter-modèles possible) :
- "predicat" : choisis UNIQUEMENT dans cette liste : {vocab}
- "sujet" et "objet" : des NOMS DE CONCEPTS de 1 à 3 mots (jamais de phrase)
Réponds UNIQUEMENT par un JSON valide, sans aucun autre texte :
{{"triplets": [{{"sujet": "...", "predicat": "...", "objet": "..."}}]}}"""


@dataclass
class RunReport:
    cycles: int = 0
    gaps_explored: List[str] = field(default_factory=list)
    proposals: int = 0                 # triplets proposés (tous modèles)
    accepted: int = 0                  # liens passés au consensus (tous niveaux)
    accepted_exact: int = 0            # accord exact (s,p,o) entre modèles
    accepted_pair: int = 0             # accord de lien (s,o), prédicats différents
    rejected: int = 0
    parse_errors: Dict[str, int] = field(default_factory=dict)   # par modèle
    nodes_added: int = 0
    edges_added: int = 0
    cochain_entries: int = 0


class EsmmOrchestrator:
    """`clients` : dict {nom_modèle: client}, chaque client expose
    `.generate(prompt, options) -> str`. Les modèles sont interrogés
    SÉQUENTIELLEMENT (rotation VRAM douce — un seul modèle chargé à la fois)."""

    def __init__(self, graph: GraphStore, clients: Dict[str, object],
                 min_agree: int = 2, gap_limit: int = 4,
                 gen_options: Optional[Dict] = None, matcher=None):
        if len(clients) < min_agree:
            raise ValueError(f"consensus impossible : {len(clients)} modèle(s) "
                             f"pour min_agree={min_agree}")
        self.graph = graph
        self.clients = dict(clients)
        self.min_agree = min_agree
        self.gap_limit = gap_limit
        self.gen_options = dict(gen_options or {"temperature": 0.4, "top_p": 0.9,
                                                "num_predict": 512})
        self.matcher = matcher    # équivalence sémantique optionnelle (cf. consensus.vote)
        self.detector = GapDetector(graph)

    # ---------- amorçage (cause racine n°1 : obligatoire, jamais implicite) ----------
    def seed(self, concepts: Sequence[str]) -> int:
        added = 0
        for c in concepts:
            cid = normalize_entity(c)
            if cid and self.graph.node(cid) is None:
                self.graph.upsert_node(cid, "concept", {"seed": True})
                added += 1
        return added

    # ---------- un cycle ----------
    def _explore_gap(self, gap: Gap) -> List[Extraction]:
        prompt = EXPLORE_PROMPT.format(concept=gap.node_id, gap_type=gap.type,
                                       detail=gap.detail,
                                       vocab=", ".join(PREDICATE_VOCAB))
        extractions: List[Extraction] = []
        for name, client in self.clients.items():   # séquentiel : rotation VRAM douce
            text = client.generate(prompt, self.gen_options)
            extractions.append(extract_triplets(name, text))
        return extractions

    def _commit(self, consensus: ConsensusResult, cycle: int, report: RunReport) -> None:
        for ct in consensus.accepted:
            t = ct.triplet
            s = normalize_entity(t.subject)
            o = normalize_entity(t.object)
            pred = normalize_entity(t.predicate) or "cooccur"
            for cid in (s, o):
                if self.graph.node(cid) is None:
                    self.graph.upsert_node(cid, "concept", {})
                    report.nodes_added += 1
            if s != o:
                before = self.graph.edge(s, o)
                self.graph.add_edge(s, o, type=pred,
                                    data={"supporters": list(ct.supporters),
                                          "consensus_level": ct.level})
                if before is None:
                    report.edges_added += 1
            # cochaîne épistémique v1 : support / diversité / sources
            for cid in (s, o):
                node = self.graph.node(cid)
                cochain = node.data.setdefault(
                    "cochain", {"support": 0, "diversity": 0, "sources": [], "updated_cycle": 0})
                cochain["support"] += len(ct.supporters)
                cochain["sources"] = sorted(set(cochain["sources"]) | set(ct.supporters))
                cochain["diversity"] = len({
                    self.graph.edge(cid, nb).type
                    for nb in self.graph.neighbors(cid)
                    if self.graph.edge(cid, nb) is not None})
                cochain["updated_cycle"] = cycle
                report.cochain_entries += 1

    # ---------- le run ----------
    def run(self, seeds: Sequence[str] = (), cycles: int = 3,
            raise_on_empty: bool = True) -> RunReport:
        if seeds:
            self.seed(seeds)
        if self.graph.counts()["nodes"] == 0:
            raise EsmmEmptyRun(
                "graphe vide et aucune graine fournie — l'ESMM ne tourne pas à blanc "
                "(cause racine n°1 de l'échec historique, désormais un refus explicite)")

        report = RunReport()
        for cycle in range(1, cycles + 1):
            report.cycles = cycle
            gaps = self.detector.detect(limit=self.gap_limit)
            if not gaps:
                break  # plus de lacunes : exploration terminée (état, pas échec)
            for gap in gaps:
                extractions = self._explore_gap(gap)
                report.gaps_explored.append(f"{gap.type}:{gap.node_id}")
                report.proposals += sum(len(e.triplets) for e in extractions)
                consensus = vote(extractions, min_agree=self.min_agree,
                                 matcher=self.matcher)
                for model, errs in consensus.parse_errors.items():
                    report.parse_errors[model] = report.parse_errors.get(model, 0) + len(errs)
                report.rejected += consensus.rejected
                report.accepted += len(consensus.accepted)
                report.accepted_exact += sum(1 for c in consensus.accepted if c.level == "exact")
                report.accepted_pair += sum(1 for c in consensus.accepted if c.level == "pair")
                self._commit(consensus, cycle, report)

        if report.accepted == 0 and raise_on_empty:
            raise EsmmEmptyRun(
                f"{report.cycles} cycle(s), {report.proposals} proposition(s), "
                f"0 triplet accepté (rejetés: {report.rejected}, "
                f"erreurs de parsing: {report.parse_errors}) — run vide, échec bruyant")
        return report
