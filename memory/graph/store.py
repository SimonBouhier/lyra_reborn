"""Nemeton — le graphe sémantique de Lyra (P3), avec deltas auditables + rollback.

Design consolidé depuis les audits (pas de copie de code source) :
- Nœuds typés + arêtes de co-occurrence pondérées : famille Uni / `IspaceNav`.
- **Deltas auditables + rollback** : design de `lyra_ACE`/`lyra_clean_bis`
  (`database/graph_delta.py`), ré-implémenté en mémoire.
- **Un seul chemin de calcul du degré** (l'audit a trouvé un double-comptage
  trigger SQL + `_update_degrees` qui faussait κ : ici, le degré EST la taille
  de l'adjacence, point).
- **Bornes dures anti-explosion** : l'audit a trouvé un état de 1,18 M d'arêtes
  (un nœud par mot, ré-sérialisé à chaque message). Ici, dépasser les bornes
  lève `GraphLimitExceeded` — échec bruyant (charte §1), pas de croissance
  silencieuse.
- `is_novel_link(a, b, k=2)` : le primitif LOCAL de nouveauté compositionnelle
  (spec `docs/METRIQUES_SONGE.md` §1d — O(deg), jamais de plus court chemin).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import time


class GraphLimitExceeded(RuntimeError):
    """Le graphe atteint sa borne — on échoue bruyamment, on ne gonfle pas en silence."""


def _edge_key(a: str, b: str) -> Tuple[str, str]:
    """Arêtes non orientées : clé normalisée."""
    return (a, b) if a <= b else (b, a)


@dataclass
class Node:
    id: str
    type: str            # ex. concept | state | intent | artifact | persona | tool
    data: Dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


@dataclass
class Edge:
    a: str
    b: str
    type: str            # ex. cooccur | led_to | supports | conflicts_with | refines
    count: int = 1       # compteur local de co-occurrence (incrémental — jamais de PMI globale)
    data: Dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


class GraphStore:
    """Graphe non orienté typé, en mémoire, avec journal de deltas et rollback."""

    def __init__(self, max_nodes: int = 50_000, max_edges: int = 500_000):
        self.max_nodes = max_nodes
        self.max_edges = max_edges
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[Tuple[str, str], Edge] = {}
        self._adj: Dict[str, Set[str]] = {}
        # journal de deltas : chaque mutation y consigne son inverse (rollback)
        self._deltas: List[Dict[str, Any]] = []

    # ---------------- mutations (toutes journalisées) ----------------

    def upsert_node(self, id: str, type: str, data: Optional[Dict[str, Any]] = None) -> None:
        prev = self._nodes.get(id)
        if prev is None and len(self._nodes) >= self.max_nodes:
            raise GraphLimitExceeded(f"max_nodes={self.max_nodes} atteint (upsert '{id}')")
        self._deltas.append({
            "op": "upsert_node", "id": id,
            "prev": None if prev is None else {
                "type": prev.type, "data": dict(prev.data), "ts": prev.ts,
            },
        })
        self._nodes[id] = Node(id=id, type=type, data=dict(data or {}))
        self._adj.setdefault(id, set())

    def add_edge(self, a: str, b: str, type: str = "cooccur",
                 data: Optional[Dict[str, Any]] = None) -> int:
        """Ajoute ou renforce une arête (incrémente `count`). Retourne le count."""
        if a == b:
            return 0  # pas de boucle sur soi
        for n in (a, b):
            if n not in self._nodes:
                raise KeyError(f"nœud inconnu '{n}' — upsert_node d'abord (pas de création implicite)")
        key = _edge_key(a, b)
        prev = self._edges.get(key)
        if prev is None and len(self._edges) >= self.max_edges:
            raise GraphLimitExceeded(f"max_edges={self.max_edges} atteint (add_edge {key})")
        self._deltas.append({
            "op": "add_edge", "key": key,
            "prev": None if prev is None else {"type": prev.type, "count": prev.count,
                                               "data": dict(prev.data), "ts": prev.ts},
        })
        if prev is None:
            self._edges[key] = Edge(a=key[0], b=key[1], type=type, data=dict(data or {}))
            self._adj[a].add(b)
            self._adj[b].add(a)
        else:
            prev.count += 1
            prev.ts = time.time()
            if data:
                prev.data.update(data)
        return self._edges[key].count

    def remove_edge(self, a: str, b: str) -> bool:
        key = _edge_key(a, b)
        prev = self._edges.pop(key, None)
        if prev is None:
            return False
        self._deltas.append({
            "op": "remove_edge", "key": key,
            "prev": {"type": prev.type, "count": prev.count,
                     "data": dict(prev.data), "ts": prev.ts},
        })
        self._adj[key[0]].discard(key[1])
        self._adj[key[1]].discard(key[0])
        return True

    # ---------------- rollback (le delta est auditable ET réversible) ----------------

    def rollback(self, n: int = 1) -> int:
        """Défait les `n` dernières mutations. Retourne le nombre défait."""
        undone = 0
        while undone < n and self._deltas:
            d = self._deltas.pop()
            if d["op"] == "upsert_node":
                if d["prev"] is None:
                    node_id = d["id"]
                    # retirer le nœud ET ses arêtes résiduelles (cohérence adjacence)
                    for other in list(self._adj.get(node_id, ())):
                        self._edges.pop(_edge_key(node_id, other), None)
                        self._adj[other].discard(node_id)
                    self._adj.pop(node_id, None)
                    self._nodes.pop(node_id, None)
                else:
                    cur = self._nodes[d["id"]]
                    cur.type = d["prev"]["type"]
                    cur.data = dict(d["prev"]["data"])
                    cur.ts = d["prev"]["ts"]
            elif d["op"] == "add_edge":
                key = d["key"]
                if d["prev"] is None:
                    self._edges.pop(key, None)
                    self._adj[key[0]].discard(key[1])
                    self._adj[key[1]].discard(key[0])
                else:
                    e = self._edges[key]
                    e.type = d["prev"]["type"]
                    e.count = d["prev"]["count"]
                    e.data = dict(d["prev"]["data"])
                    e.ts = d["prev"]["ts"]
            elif d["op"] == "remove_edge":
                key = d["key"]
                p = d["prev"]
                self._edges[key] = Edge(a=key[0], b=key[1], type=p["type"],
                                        count=p["count"], data=dict(p["data"]),
                                        ts=p["ts"])
                self._adj[key[0]].add(key[1])
                self._adj[key[1]].add(key[0])
            undone += 1
        return undone

    def deltas(self) -> List[Dict[str, Any]]:
        """Journal auditable (lecture seule — copie)."""
        return list(self._deltas)

    # ---------------- lectures ----------------

    def node(self, id: str) -> Optional[Node]:
        return self._nodes.get(id)

    def list_nodes(self, type: Optional[str] = None, limit: int = 200) -> List[Node]:
        out = [n for n in self._nodes.values() if type is None or n.type == type]
        out.sort(key=lambda n: n.ts, reverse=True)
        return out[:limit]

    def neighbors(self, id: str) -> Set[str]:
        return set(self._adj.get(id, ()))

    def degree(self, id: str) -> int:
        """LE degré — unique chemin de calcul (cf. bug de double-comptage audité)."""
        return len(self._adj.get(id, ()))

    def edge(self, a: str, b: str) -> Optional[Edge]:
        return self._edges.get(_edge_key(a, b))

    def counts(self) -> Dict[str, int]:
        return {"nodes": len(self._nodes), "edges": len(self._edges)}

    # ---------------- primitifs pour le Songe (locaux, bornés) ----------------

    def common_neighbors(self, a: str, b: str) -> Set[str]:
        return self.neighbors(a) & self.neighbors(b)

    def is_novel_link(self, a: str, b: str, hub_degree_cap: Optional[int] = None) -> bool:
        """Nouveauté compositionnelle à profondeur k=2 (METRIQUES_SONGE §1d).

        Lien « neuf » ssi : pas d'arête directe ET aucun voisin commun. Calcul
        LOCAL en O(deg) — jamais de plus court chemin ni de PMI globale.
        `hub_degree_cap` : si fourni, les voisins communs qui sont des hubs
        (degré > cap) sont ignorés — garde-fou anti-densification signalé lors
        du gel de la spec (un hub finit par relier tout à 2 sauts).
        """
        if a == b or a not in self._nodes or b not in self._nodes:
            return False
        if self.edge(a, b) is not None:
            return False
        common = self.common_neighbors(a, b)
        if hub_degree_cap is not None:
            common = {c for c in common if self.degree(c) <= hub_degree_cap}
        return len(common) == 0

    # ---------------- entretien & sérialisation bornée ----------------

    def compact(self, min_count: int = 2) -> int:
        """Élague les arêtes de co-occurrence faibles (count < min_count).

        Retourne le nombre d'arêtes retirées (journalisées → rollback possible).
        C'est l'outil anti « un nœud par mot » : le bruit à count=1 ne survit pas.
        """
        weak = [k for k, e in self._edges.items() if e.count < min_count]
        for key in weak:
            self.remove_edge(key[0], key[1])
        return len(weak)

    def snapshot(self, max_bytes: int = 2_000_000) -> str:
        """Sérialise l'état (JSON). Refuse bruyamment de produire un monstre.

        (L'audit a trouvé un `last_state.json` de plusieurs centaines de Mo,
        ré-écrit à chaque message. Ici : au-delà de `max_bytes`, on lève —
        c'est le signal qu'il faut `compact()` d'abord.)
        """
        payload = {
            "nodes": [{"id": n.id, "type": n.type, "data": n.data, "ts": n.ts}
                      for n in self._nodes.values()],
            "edges": [{"a": e.a, "b": e.b, "type": e.type, "count": e.count,
                       "data": e.data, "ts": e.ts}
                      for e in self._edges.values()],
        }
        s = json.dumps(payload, ensure_ascii=False)
        if len(s.encode("utf-8")) > max_bytes:
            raise GraphLimitExceeded(
                f"snapshot > {max_bytes} octets — compact() avant de sérialiser")
        return s

    @classmethod
    def from_snapshot(cls, s: str, **kwargs) -> "GraphStore":
        g = cls(**kwargs)
        payload = json.loads(s)
        for n in payload["nodes"]:
            g.upsert_node(n["id"], n["type"], n["data"])
            g._nodes[n["id"]].ts = n["ts"]
        for e in payload["edges"]:
            g.add_edge(e["a"], e["b"], e["type"], e["data"])
            restored = g._edges[_edge_key(e["a"], e["b"])]
            restored.count = e["count"]
            restored.ts = e["ts"]
        g._deltas.clear()  # un chargement n'est pas une mutation à rejouer
        return g
