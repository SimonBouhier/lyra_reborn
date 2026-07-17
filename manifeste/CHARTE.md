# Charte méthodologique de Lyra

Chaque règle neutralise une pathologie **observée et datée** dans les audits des
deux lots de prototypes. Elles ne sont pas décoratives : le CI et la revue les
appliquent.

1. **Anti « vert mais vide ».** Tout pipeline censé produire quelque chose a un
   test qui **échoue bruyamment** si le résultat est vide/trivial.
   *(Cas fondateurs : ESMM 0 triplet sur 71 cycles « réussis » ; base ACE vide ;
   simulateur de tensions 0 arête ; nuit du 26/03/2025 où un GA réel fut remplacé
   par des simulacres `np.random`.)*

2. **Pas de `except` avaleur.** `except Exception: pass` est interdit. On
   log-et-relève, ou on attrape étroitement.
   *(Cause racine directe du bug ESMM et de la relecture cassée de l'écologie
   mémorielle.)*

3. **Modulation prouvée.** Toute « modulation » a un test : mêmes entrées + deux
   réglages ⇒ paramètres **différents** ET sorties **différentes**.
   *(Cas : Lyra_Core où seul τc agissait ; ρ/δr/κ n'étaient que du texte.)*

4. **Doc = réalité reproductible.** Un chiffre dans un doc ⇒ un script du dépôt le
   régénère. Sinon, section « Vision/Cible » explicite.
   *(Cas : −53 % tokens, R²=0,89 codé en dur, « 92 % Production Validée »,
   15 234 concepts.)*

5. **Une idée, une implémentation.** Avant d'écrire une brique, `grep` le dépôt :
   si elle existe, on l'étend, on ne la duplique pas.
   *(Cause : 3 à 6 copies de chaque brique dans les archives.)*

6. **Secrets hors code.** Clés/API par variables d'environnement uniquement
   (`.env` git-ignoré). Jamais de `eval()` sur une sortie LLM.
   *(Cas : 3 clés OpenAI en clair dans les archives ; `eval()` sur sortie LLM dans
   LyrAgent.)*

## Definition of Done (générique)

> code + **test qui prouve l'effet réel** + une ligne de doc reproductible +
> zéro `except` avaleur introduit.

## Honnêteté épistémique

À ce jour, **aucune** brique ne prouve « conscience » ni supériorité mesurée. On
distingue toujours : *acquis* (démontré par un test/chiffre reproductible) vs
*cap* (intention à démontrer). Le survendre serait rejouer la maladie n°1.
