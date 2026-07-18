"""Détection de lacunes (gaps) dans le nemeton — le déclencheur de l'exploration.

Taxonomie de l'audit `lyra_clean_bis` (isolated / unstable / bridge /
contradiction), implémentée sur ce que notre graphe sait réellement mesurer —
tout en calculs LOCAUX :
- **isolated**      : concept sans aucun lien (degré 0) ;
- **unstable**      : concept dont TOUS les liens sont faibles (count == 1) ;
- **bridge**        : concept dont les voisins ne se connaissent pas entre eux
                      (clustering local nul avec degré ≥ 2) — un pont fragile ;
- **contradiction** : arête typée `conflicts_with` non résolue.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from typing import List

from memory.graph.store import GraphStore


@dataclass
class Gap:
    type: str          # isolated | unstable | bridge | contradiction
    node_id: str       # concept concerné (ou l'un des deux pour contradiction)
    detail: str


class GapDetector:
    def __init__(self, graph: GraphStore, max_bridge_degree: int = 12):
        self.graph = graph
        # au-delà de ce degré, le test de clustering local coûte trop cher et un
        # hub n'est de toute façon pas un « pont fragile » — on passe.
        self.max_bridge_degree = max_bridge_degree

    def detect(self, limit: int = 10) -> List[Gap]:
        gaps: List[Gap] = []
        g = self.graph

        for node in g.list_nodes(limit=10_000):
            if len(gaps) >= limit:
                break
            nid = node.id
            deg = g.degree(nid)
            if deg == 0:
                gaps.append(Gap("isolated", nid, "aucun lien"))
                continue
            neigh = g.neighbors(nid)
            edges = [g.edge(nid, o) for o in neigh]
            if edges and all(e is not None and e.count == 1 for e in edges):
                gaps.append(Gap("unstable", nid, f"{deg} lien(s), tous faibles (count=1)"))
                continue
            if 2 <= deg <= self.max_bridge_degree:
                pairs = list(combinations(sorted(neigh), 2))
                if pairs and all(g.edge(a, b) is None for a, b in pairs):
                    gaps.append(Gap("bridge", nid,
                                    f"pont : {deg} voisins mutuellement inconnus"))

        # contradictions : arêtes typées conflicts_with
        for node in g.list_nodes(limit=10_000):
            if len(gaps) >= limit:
                break
            for other in g.neighbors(node.id):
                e = g.edge(node.id, other)
                if e is not None and e.type == "conflicts_with" and node.id < other:
                    gaps.append(Gap("contradiction", node.id,
                                    f"conflit non résolu avec '{other}'"))
        return gaps[:limit]
