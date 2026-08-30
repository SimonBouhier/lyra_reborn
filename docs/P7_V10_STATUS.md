# P7 — statut de la campagne V10

**Préinscription gelée :** `bc8497f6bb083ff2c27632ded784e13ea264cc5d`
(`PREREGISTRATION_v10.md`), estampille `f6c8ba5`

**Amendements :** `docs/P7_V10_PRERUN_AMENDMENT.md` (`23fa1cc`, portée
épistémique) ; `docs/P7_V10_PRODUCER_CONTEXT_AMENDMENT.md` (`c5e457d`,
fenêtre producteur)

**Verdict de campagne : `V10_ARRETEE_APRES_Q0` — `H10 UNTESTED`.**

Q0 est franchie. Aucune autre porte n'a été ouverte : la calibration ne s'est
jamais verrouillée, le jeu tenu n'a jamais été lu, aucun verdict H10 n'existe.
Décision de Simon Bouhier du 2026-08-30, sur dérive du runtime.

## Ce qui est acquis : Q0

**Exécution :** `p7_v10_q0_20260829T211254.467768Z`, verrou
`p7_v10_q0_bc8497f6bb083ff2c27632ded784e13ea264cc5d.lock`
**Statut :** `Q0_PASSED` — 18/18
**Journal :** `6373f4692051162ab34884a1dc90674d74a7cb024ea1e1393bd97ac7a5d60a4a`

Les 18 appels satisfont simultanément les conditions gelées : wire-clean
(HTTP 200, `response` non vide, `thinking` vide, `done_reason=stop`), contrat
réduit validé, références résolues, préférence égale à l'attendu, unanimité
des trois répétitions dans chacune des six cellules, invariance logique après
inversion sur les trois fixtures.

Avant et après le bloc, Ollama **0.32.15** rapporte pour `qwen3.8:27b` le
digest gelé `22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643`
et `size_vram == size > 0` au contexte 32 768.

C'est la **première porte franchie du programme P7** après huit arrêts
consécutifs (V3→V10). Elle établit un fait limité mais réel : sous le contrat
réduit et le transport gelés, `qwen3.8:27b` reproduit les attendus des trois
fixtures V8 dans les deux orientations, trois fois chacune, sur le moteur
0.32.15. Elle n'établit rien sur H10.

## Cause de l'arrêt

Deux incidents distincts, tous deux détectés **avant** le verrou de
calibration, donc sans consommer un seul appel.

### 1. Fenêtre des producteurs (résolu par amendement)

Ollama monte un modèle à son contexte maximum quand la requête ne demande pas
de `num_ctx` — et le mapping producteur gelé n'en demande aucun.
`granite3.3:latest` à 131 072 pèse 27,70 Go dont 22,77 Go seulement en VRAM sur
une carte de 24 Go. La précondition `size_vram == size` a refusé.

Résolu par `docs/P7_V10_PRODUCER_CONTEXT_AMENDMENT.md` : fenêtre producteur
fixée à 32 768 au niveau du serveur. Vérifié ensuite sur le serveur réel — les
quatre modèles montent à 32 768 avec `size_vram == size`, granite passant de
27,70 Go à 10,58 Go. **Cet incident n'est pas la cause de l'arrêt.**

### 2. Dérive du runtime (cause de l'arrêt)

Le 2026-08-30 à 00 h 24, environ une heure après la fin de Q0, Ollama s'est
mis à jour automatiquement de **0.32.15** — version épinglée par la prérég
§Scope/Runtime et sur laquelle Q0 a intégralement tourné — vers **0.33.2**.

Poursuivre aurait fait chevaucher deux moteurs à la campagne : le juge
qualifié sur l'un, H10 mesurée sur l'autre. Or Q0 est la « qualification du
juge **en condition de campagne** » ; si les conditions changent après elle,
elle ne certifie plus rien de ce qui est mesuré. Et la re-qualifier est
impossible : le gel interdit toute seconde tentative.

Trois issues étaient ouvertes : revenir en 0.32.15 ; consigner l'écart et
poursuivre ; arrêter et repréinscrire. La deuxième aurait laissé, dans la note
de résultats, un juge qualifié sur un moteur et une hypothèse mesurée sur un
autre — un trou qu'aucune formulation ne referme. **Simon a choisi l'arrêt et
une V11 cohérente de bout en bout.**

## Ce que l'arrêt préserve

Aucune donnée n'a été dépensée au-delà de Q0 :

- les **12 cas de calibration** n'ont jamais été ouverts ;
- les **60 cas tenus** n'ont jamais été lus ni générés — le jeu tenu reste
  intact, ce qui est la condition d'une V11 confirmatoire ;
- aucun appel producteur n'a été émis, aucun pack n'a été construit ;
- les plafonds (432/432/900/360) sont intacts.

Le harnais reste valide comme ingénierie, indépendamment du verdict
scientifique (prérég §« La continuation d'ingénierie reste valide ») : noyau
juge unique, sélection et scellement du corpus, logique de calibration,
scoreur C0–C12, exécuteurs des trois phases, scoreur global, smoke de cycle de
vie, et l'ensemble de ses tests hors-ligne.

## Leçons portées à V11

1. **Le runtime doit être tenu, pas seulement épinglé.** V10 l'épinglait sans
   le vérifier : le préflight avertissait, les phases ne regardaient rien.
   Corrigé (`1eb1351`) — un écart arrête chaque phase avant son verrou et est
   revérifié autour de chaque bloc. V11 doit en outre **empêcher** la mise à
   jour automatique pendant la campagne, pas seulement la détecter.
2. **Les paramètres d'exploitation implicites sont des paramètres.** La
   fenêtre des producteurs n'était fixée nulle part ; son défaut rendait le
   design inexécutable. V11 la spécifie dès le gel.
3. **La chaîne doit pouvoir reprendre sans rejouer une phase close.** Règle
   introduite par l'amendement §4, à intégrer directement au gel V11.
