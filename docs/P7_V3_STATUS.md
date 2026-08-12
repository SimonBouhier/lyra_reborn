# P7 V3 — arrêt avant mesure

**Date :** 2026-08-12
**Statut :** `V3_ABORTED_BEFORE_HELDOUT`
**Hypothèse H3 :** non testée ; aucun verdict scientifique.

## Ce qui a été exécuté

Uniquement le smoke-test synthétique documenté dans
`docs/P7_VERTICAL_SLICE.md`, avec `mistral:latest` au digest gelé
`6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf`,
Ollama 0.32.9 et le cas `synthetic:live:1`.

Aucun cas principal n'a été sélectionné, scellé, affiché ou généré. Le corpus
tenu reste fermé. Le smoke ne constitue donc ni une observation O1–O12, ni une
tentative de soutenir ou réfuter H3.

## Invariant invalidé

V3 donnait aux deux bras le même prompt, les mêmes options et la même graine au
tour 1, puis supposait que leur sortie serait identique afin d'attribuer la
première divergence à la politique.

Le smoke a observé :

- prompt et options de tour 1 identiques ;
- sortie ADAPTIVE : 1 100 caractères, SHA-256
  `fa8218566ee5042c14ed03b4fa8f2b427ad27d16cd9028f9bb523110636a4141` ;
- sortie STATIC_BEST : 1 306 caractères, SHA-256
  `8daa9081bf104f287bd1106b74c901d28fbdd00df0b4a1b2a8ef25d70a9f8940`.

Une sonde directe hors harnais a ensuite envoyé deux payloads Ollama identiques
(`temperature=0.98`, `top_p=0.59`, `repeat_penalty=1.3`, `num_predict=64`,
`seed=1529387622`). La comparaison byte-à-byte a rendu `false`, avec 337 et 344
caractères. La graine ne supprime donc pas le bruit de génération sur ce runtime.

Le contrat final a aussi rejeté la trace ADAPTIVE pour citation absente de la
source, tandis que STATIC_BEST l'a satisfaite. Ce contrôle est sain, mais ce
résultat synthétique n'entre pas dans H3.

## Décision méthodologique

`PREREGISTRATION_v3.md` reste immuable. Sa clause anti-confirmation impose une
nouvelle préinscription puisque la correction touche l'unité d'exécution.

V4 devra :

1. générer le tour 1 une seule fois par cas/modèle ;
2. donner ce préfixe observé identique aux deux branches ;
3. laisser ADAPTIVE mettre à jour son état à partir de cette observation, et
   garder STATIC_BEST constant ;
4. exécuter les branches 2–3 dans un ordre déterministe contrebalancé ;
5. traiter le résidu stochastique comme du bruit expérimental, pas comme une
   preuve de modulation ;
6. conserver le test synthétique contrôlé comme preuve distincte que des
   options différentes peuvent produire des sorties différentes.

V3 n'est pas « négative ». Elle est invalide avant mesure, ce qui est précisément
le rôle du smoke-test précoce.
