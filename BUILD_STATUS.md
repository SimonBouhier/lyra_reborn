# BUILD STATUS — index des composants et de leur provenance

**Alignement : 9 septembre 2026.** Cet index permet de retrouver les briques,
leurs sources de conception et leurs documents. La disponibilité et les limites
font autorité dans [ETAT_ACTUEL](docs/ETAT_ACTUEL.md) ; l'ordre des chantiers
relève du [PLAN_EDIFICATION](docs/PLAN_EDIFICATION.md). Les statuts de campagne
conservent leurs verdicts propres. Cet index ne prononce aucun degré de maturité.

## Composants et sources

Les noms de prototypes ci-dessous sont des références historiques de conception,
pas des chemins locaux garantis ni des dépendances à installer. Le
[registre des intentions](docs/REGISTRE_INTENTIONS.md) et l'index des
[sources ouvrables](docs/00_SOURCES_OUVRABLES.md) en conservent la traçabilité.

| Repère | Composants ou emplacement | Provenance et document d'orientation |
|---|---|---|
| P0 — cadre et configuration | [Charte](manifeste/CHARTE.md), [vocabulaire](manifeste/VOCABULAIRE.md), [pyproject](pyproject.toml) | Plan directeur et audits fondateurs |
| P0 — boutons et moteur | [knobs.py](core/knobs.py), [llm.py](core/llm.py) | `conscious/config.py`, `bundle_lyra/gemma_bridge_v2.py` ; mapping unique et transmission de `options{}` |
| P1 — mesures et état | [cheap.py](core/metrics/cheap.py), [state.py](core/state.py), [guards.py](core/control/guards.py) | `conscious/metrics/cheap.py`, `guards.py`, `state.py` ; métriques textuelles, bornes, hystérésis, réfractaire et EWMA |
| P1 — contrôle | [reactive.py](core/control/reactive.py), [controller.py](core/control/controller.py), [loop.py](core/loop.py) | `conscious/policies/modulator.py`, `lyra_framework_bundle/src/run_loop3.py` ; [atelier B03/P1P2](docs/STARTER_KIT_ATELIER_B03_P1P2.md) |
| P2 — pont et phase | [bridge.py](core/control/bridge.py), [phase.py](core/control/phase.py), [measures.py](core/control/measures.py) | Pont de génération, politique λ et démonstration synthétique ; leurs rôles distincts sont décrits dans [ETAT_ACTUEL](docs/ETAT_ACTUEL.md#correspondance-entre-les-organes-et-le-code) |
| P2 — topologie | [core/topology/](core/topology/) | Décision Simon du 18 juillet conservée dans le plan ; l'ancien pipeline n'est pas une consigne de portage |
| P3 — Nemeton | [GraphStore](memory/graph/store.py), [injecteur](memory/graph/injector.py) | Designs `lyra_ACE`/`lyra_clean_bis` et famille Uni ; deltas, bornes, compaction et primitive structurelle `is_novel_link` |
| P3 — écologie | [MemoryEcology](memory/ecology/ecology.py) | Design `session_2/LyrArc` ; pouponnière mémorielle, oubli différé, compost et réveil ; distinct de la Pouponnière évolutive |
| P3 — ispace et cas | [Memento / Navigator](memory/cbr/memento.py) | Design `session_2/IspaceNav.zip` ; rappel de cas et cibles de navigation à champs explicites |
| P4 — exploration | [explore/esmm/](explore/esmm/), [embeddings](core/embeddings.py) | `lyra_clean_bis/services/esmm` ; éléments historiques de consensus issus d'EPP_Verdict ADR-011-v2 / ADR-006, sans ouverture de pont inter-projets |
| Affect | [affect.py](core/affect.py) | Esquisse Simon du 19 juillet et canon `conscious` ; affichage dérivé des signaux du pont |
| P5 — outils, modules et SilenceØ | [agency/tools/](agency/tools/) | Design `session_2/LyrAgent` et [plan](docs/PLAN_EDIFICATION.md) ; pas de `eval()` sur une sortie de modèle |
| P6 — profil historique et état | [session.py](app/session.py), [storage.py](app/storage.py), [main.py](app/main.py) | Parcours contrôle/mémoire et persistance ; [premières couches](tests/test_p6_first_layers.py), [persistance](tests/test_session_persistence.py) |
| P6 — journal et demandes | [journal.py](app/journal.py), [requests.py](app/requests.py), [client](app/static/p6-ui.js) | [A01](docs/P6_A01_CONCURRENCE_2026-09-07.md), [journal et demandes](docs/P6_JOURNAL_DEMANDES_2026-09-07.md) |
| P6 — dialogue de référence | [dialogue.py](app/dialogue.py), [context.py](app/context.py), [dialogue_store.py](app/dialogue_store.py), [chat_backend.py](app/chat_backend.py) | [Contrat d'usage](docs/CONTRAT_USAGE_P6_v0_2026-09-07.md), [contexte, corrections et rappels](docs/P6_CONTEXTE_CORRECTIONS_RAPPELS_2026-09-08.md) |
| P6 — diagnostic séparé | [experiments/p6_recall/](experiments/p6_recall/), [guide d'exécution](experiments/p6_recall/README.md) | [Diagnostic des rappels](docs/P6_DIAGNOSTIC_RAPPELS_2026-09-08.md), [exports](docs/P6_RAPPEL_EXPORTS_2026-09-08.md), [mode d'emploi de relecture](docs/P6_RELECTURE_MODE_EMPLOI_2026-09-08.md) |
| P6 — autres interfaces | [app/](app/) | `lyra_clean_bis` demeure un matériau d'audit ; suppression, sauvegardes et autres jalons sont décrits dans le contrat et le plan |
| P7 — évaluation | [eval/](eval/), [runner V11](scripts/p7_v11.py) | [Statut V11](docs/P7_V11_STATUS.md), [cadrage post-V11](docs/CADRAGE_EXTERNE_P6_P7_POST_V11.md) ; protocoles et empreintes restent des preuves historiques distinctes |
| Recherche | [research/](research/) | `session_2/tranzit` : orbites FLOATLAP, métriques fractales et calibrations ; intentions dans le registre |
| Vigie — frontière spécifique | [quarantine.py](agency/tools/vigie/quarantine.py) | [Vigie](docs/LA_VIGIE.md), [quarantaine](docs/VIGIE_QUARANTINE.md), [doctrine de l'Architecte](manifeste/DOCTRINE_ARCHITECTE.md) |

## Intentions, Jachère et liens entre organes

- [Bannière La Jachère](docs/BANNIERE_LA_JACHERE.md) : entrée des travaux hors tâche.
- [Note Jachère du 7 septembre](docs/NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md) : orientation actuelle des fonctions autonomes, droits, échanges, budgets, admission et retrait.
- [Métriques du Songe](docs/METRIQUES_SONGE.md) et [traces résiduelles](docs/ESSAI_TRACES_RESIDUELLES.md) : propositions et filiation ; leur statut courant est donné par [ETAT_ACTUEL](docs/ETAT_ACTUEL.md#jachère-songe-et-fonctions-futures).
- [Registre des intentions](docs/REGISTRE_INTENTIONS.md) : consolidation, recombinaison, Pouponnière évolutive, oubli, intériorité, transformation paramétrique et questions ouvertes.
- [Organes et ponts](docs/ORGANES_ET_PONTS.md) : doctrine inter-projets et résultats historiques à respecter, sans disponibilité inter-dépôts déduite de leur citation.
- [Charte de transformation](manifeste/CHARTE_TRANSFORMATION.md) : texte candidat conservé ; provenance dans la [carte des branches](docs/BRANCHES.md).

L'ancien inventaire rattachait la Pouponnière évolutive aux références
`2607.13104v1`, `2607.06906v1`, `2607.14159v1`, au design LyrArc et à NSGA-II
Lyra_Core ; il rattachait le Songe à *Language Models Need Sleep*, Nemeton,
FLOATLAP et aux phases κ/ρ. Ces filiations restent consultables dans l'archive
ci-dessous et le registre. Elles ne valent pas vérification des articles ni
preuve d'une identité de mécanisme locale. La maison envisagée `evolve/` et
l'horizon d'entraînement local restent des destinations du plan, pas des
composants que cet index annoncerait disponibles.

## Archive et filiation

La [version antérieure de BUILD_STATUS](BUILD_STATUS_2026-09-09_AVANT_ALIGNEMENT.md)
est une **archive historique, sans autorité sur la disponibilité actuelle**.
Elle conserve l'inventaire intégral, les décisions datées, les anciennes
formulations de maturité, les résultats rapportés et les noms de sources.
Ses expressions telles que « métriques figées » doivent être lues comme des
formulations antérieures, remplacées pour le statut courant par
[ETAT_ACTUEL](docs/ETAT_ACTUEL.md) et la note Jachère du 7 septembre.

- Source : `BUILD_STATUS.md` au commit
  `15bcede4d1b876821524dd1f6d53c51879497c6a`.
- Copie locale réalisée le 9 septembre 2026 avant remplacement de cet index,
  avec contenu identique octet par octet, y compris ses fins de ligne.
- SHA-256 du fichier source local et de l'archive :
  `3ad7b16ae1e2dad88945201884bb0d1deaf8a03330fe33b1334c3a80bce314bc`.
- Archive laissée à la racine pour conserver la base de ses liens relatifs.
  Les références historiques introuvables et les traces locales ignorées ne
  deviennent pas des téléchargements publics par leur présence dans un lien.
- Successeur documentaire : le présent index pour les emplacements,
  [ETAT_ACTUEL](docs/ETAT_ACTUEL.md) pour la disponibilité,
  [PLAN_EDIFICATION](docs/PLAN_EDIFICATION.md) pour la suite.

Les références `../../audits_en_cours/`, les prototypes et les audits anciens
mentionnés par l'archive sont des pistes historiques. Leur résolution appartient
à l'inventaire des sources ; elles ne doivent pas conduire à transplanter un
prototype sans lire l'audit pertinent.
