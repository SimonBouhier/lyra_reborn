# La Vigie — veille et contribution épistémique (POC d'acquisition)

> *Nom de travail* (la vigie : celle qui, en haut du mât, observe le large et
> rend le navire visible) — à rebaptiser librement.
> **Source :** doctrine de l'Architecte (`manifeste/DOCTRINE_ARCHITECTE.md`, §3).
> **Statut :** spécification raffinée à partir de l'ébauche de Simon
> (2026-07-19). Cap d'application n°1 de lyra_reborn hors laboratoire.

## Mission

Démontrer publiquement les capacités du système sur des sujets techniques de
développement IA, via une **communication assistée sur X** : le pipeline
automatise tout **jusqu'au brouillon** ; l'humain est le bouton de
publication. Construire du réseau autour de la thèse d'orchestration.

**Non-buts (durs) :** confrontation automatisée ; ciblage de comptes ou de
personnes ; publication sans validation ; croissance pour la croissance.

## Périmètre de veille

- **Sujets :** machine learning, RAG & AI agent development, generative AI,
  et tout ce qui résonne avec la thèse EPP (orchestration > capacité brute).
- **Déclencheurs typiques :** une interview publique (ex. Karpathy), un papier
  arXiv (ex. Stanford), une affirmation structurelle sur la fiabilité d'un
  système multi-modèles.
- **Règle absolue :** la cible est l'affirmation ou l'idée, **jamais la
  personne qui l'a postée**.

## Architecture — deux files, deux barèmes

```
ENTRÉES (v0 : 100 % gratuites)          FILES DE PRODUCTION
  arXiv API (gratuite)          ┌─► AUDIT (EPP via pont ; v1 = audit-léger local)
  RSS blogs de labs             │     critères : falsifiabilité de l'affirmation
  captures manuelles de Simon ──┤     (vérifiable, pas une opinion) + enjeu/écho
  (coller URL/texte d'un post)  │     (audience significative, pas du bruit anonyme)
                                └─► AMPLIFICATION (Lyra)
                                      critère : score de résonance thématique
                                      (cosinus mxbai vs corpus de thèse EPP/orchestration)
                                      sortie : une ADDITION technique, pas un accord
                        ▼
              FILE DE BROUILLONS (aucun accès réseau en écriture)
              chaque brouillon = {file, texte, score de confiance,
                                  justification courte du critère}
                        ▼
              VALIDATION HUMAINE (Simon publie à la main)
              accepté/rejeté journalisé → labels de calibration
```

- **File Audit** — EPP_Verdict évalue la solidité épistémique d'une
  affirmation publique et identifie les failles conceptuelles. Passe par le
  **pont** (doctrine ORGANES_ET_PONTS : dégel sur validation ; en attendant,
  v1 = audit-léger local par consensus multi-modèles ESMM).
- **File Amplification** — Lyra identifie les contenus qui résonnent avec la
  thèse et produit une **addition technique** (angle nouveau, précision,
  conséquence non dite) — jamais un simple accord.
- **Score + justification sur chaque brouillon** : la validation humaine reste
  rapide sur l'évident, concentrée sur l'ambigu (doctrine §2).

## Frontière amont — quarantaine des entrées

Tout contenu externe est une donnée hostile potentielle avant d'être une idée.
La frontière `agency/tools/vigie/quarantine.py` sépare le verdict de sécurité
`PASS/QUARANTINE/REJECT/ESCALATE` du verdict éditorial
`IGNORE/DEFER/AUDIT/AMPLIFY`. Le premier pont vers EPP est un subprocess sans
shell, sans secrets hérités et à schéma JSON fermé ; toute anomalie met le cas
en quarantaine. Il ne possède aucune référence vers Nemeton ou Memento.

La validation humaine ci-dessous porte sur la **publication** et, pendant la
montée en charge, sur les escalades et un échantillon de contrôle — pas sur
chaque entrée. Phasage et limites : `docs/VIGIE_QUARANTINE.md`.

## Validation humaine — règle non négociable, encodée en dur

**Aucune publication automatique.** Concrètement, dans le code : le système
n'a **aucun accès en écriture à X** — v0/v1 n'utilisent AUCUNE API X (ni
lecture ni écriture) ; la sortie est une file de brouillons locale ; Simon
copie, ajuste s'il veut, publie. Test associé : aucun secret/token X dans
l'environnement du pipeline. C'est aussi ce qui rend le POC conforme aux
règles d'automatisation de X et **gratuit** (l'API lecture est chère).

## La Jachère Sociale

Capacité à ingérer un concept émergent bruyant, à le **différer dans le
Nemeton sans réagir à la hype**, pour produire une analyse asynchrone plus
mature. Implémentation : mapping direct sur `memory/ecology` — le sujet chaud
entre au **journal d'oubli** avec `revisit_at` (échéance de réévaluation à
froid) ; s'il tient encore à l'échéance, il mérite l'analyse ; sinon il
composte avec la hype. L'écologie existante EST la jachère sociale.

## Signature de sortie

Le mapping des boutons impose le ton : profil de tâche **« clinique »**
(κ haut = anti-répétition stricte, τc bas-moyen = tension contenue, ρ moyen-haut
= structure, δr bas = concision format court). Règles : ton clinique et direct,
**zéro remplissage social artificiel** ; une pointe d'ironie sèche tolérée
occasionnellement, jamais systématique — le système doit transpirer
l'exactitude, pas la posture.

## La boucle de calibration — et le pont vers la Jachère

Chaque accepté/rejeté de Simon est **journalisé comme label**. Usages :
1. Ajustement itératif des barèmes (volume réel de faux positifs) ;
2. ⭐ **Premier flux de fitness RÉEL pour la Pouponnière** (Jachère, organe 1) :
   les harness de production de brouillons deviennent cultivables sur
   l'accept-rate de l'Architecte. La Vigie n'est pas qu'une application —
   c'est le terrain d'entraînement de l'auto-amélioration.

## Risques identifiés (red-team, à l'initiative de la revue)

1. **Perception « bot de correction »** : un compte neuf qui démarre en
   auditant des affirmations de comptes à forte audience sera lu comme
   agressif, quelle que soit la justesse. Recommandation de séquencement :
   **amplification majoritaire au démarrage**, file audit montée en puissance
   quand la crédibilité du compte est établie. *Décision Simon.*
2. **Politique d'automatisation X** : v0/v1 sans API = zéro exposition. Si un
   jour l'API lecture est ajoutée (V3), rester strictement dans les règles ;
   jamais de réponses non sollicitées en masse.
3. **Calibration des barèmes** : le seuil de résonance et les critères d'enjeu
   produiront des faux positifs au début — c'est prévu (boucle de labels), ne
   pas sur-corriger sur les 10 premiers cas.
4. **Constance de ton** : l'ironie sèche « occasionnelle » doit être une
   décision par-brouillon visible dans la justification, pas un tic.
5. **Injection/empoisonnement** : un texte externe peut viser explicitement le
   modèle ou jouer les métriques. Aucun texte brut ne rejoint la mémoire
   durable ; EPP opérera d'abord en shadow sur base éphémère, puis en probation.

## Definition of Done (V0, anti-vide)

Une passe de veille sur N entrées (arXiv/RSS/captures) produit ≤ K brouillons,
chacun avec `{file, texte ≤ contraintes du format, score, justification}` ;
**zéro appel réseau en écriture** (testé) ; les labels de Simon sont
journalisés. Échec bruyant si une passe ne produit ni brouillon ni raison
explicite de silence (le silence est un verdict légitime : « rien ne mérite
réponse » — mais il se déclare).

## Phasage

| Version | Contenu | Dépendances |
|---|---|---|
| **V0-q** | frontière de quarantaine locale, fail-closed ; sidecar EPP sans accès mémoire ni outil d'action | contrats Lyra et EPP faits ; modèles live à qualifier |
| **V0** | ingestion arXiv/RSS/captures + score de résonance (mxbai) + brouillons file Amplification + file de validation avec labels | P3 (fait), embeddings (fait), V0-q |
| **V1** | Jachère Sociale (écologie) + audit-léger local (ESMM VERIFY-lite) + profil de ton « clinique » | P4 (fait), P1 (fait) |
| **V2** | pont EPP réel pour la file Audit (doctrine des ponts : dégel sur validation) | EPP + pont |
| **V3** | lecture X par API si budget ; jamais d'écriture automatique | budget |

## Place dans le plan

Nouveau cap d'application (§8·ter du plan directeur). Il **tire** P5 (outils
d'ingestion), P7 (le juge pairwise peut pré-évaluer les brouillons) et la
Jachère (fitness réelle). Il ne déplace pas Origa (campagne v5 en cours de
gel — chantier scientifique prioritaire à part).
