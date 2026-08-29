# P7 — admission diagnostique de Gemma 3 (banc A de la règle méta)

**Nature :** banc d'ingénierie synthétique, non confirmatoire
**Langue :** anglais uniquement
**Gel initial :** `TO_BE_STAMPED`

## Place dans la règle méta

Ce banc est le **banc A** de `docs/P7_META_ARRET.md` (gel
`89d22f9b2fa36f3331d855a4288cf06dea888a95`) : premier des deux bancs restants
du design bi-juge. Tout résultat autre que « admis » — y compris une
invalidation d'intégrité après verrou — consomme le banc et active les
conditions de bascule de la règle méta. Aucune seconde tentative, aucun
candidat de substitution.

## Objectif autorisé

Déterminer si l'artefact Ollama local `gemma3:27b` peut être nommé comme
second juge candidat dans la conception V10, aux côtés de `qwen3.8:27b`
(admis par `docs/P7_QWEN38_ADMISSION_V2.md`, qualifié seul en Q-1). Ce banc
ne teste ni H10 ni le panel et n'autorise aucun accès à la calibration ou au
jeu tenu.

L'artefact est gelé par son digest
`a418f5838eaf7fe2cfe0a3046c8384b68ba43a4435542c942f9db00a5f342203` :
27,4 B, famille Ollama `gemma3`, quantification `Q4_K_M`, capacités
`completion, vision` — sans canal de raisonnement.

## Matrice et budget — même épreuve que le candidat précédent

Le banc réutilise exclusivement les huit orientations anglaises du banc
d'admission Qwen 3.8 : quatre fixtures publiques (`TRANSPORT_PARITY`,
`SEMANTIC_DOMINANCE`, `STYLE_PARITY`, `INJECTION_RESISTANCE`), deux
orientations chacune, générées avec la **même graine `20260817`** — chaque
candidat au panel passe exactement le même examen. Trois répétitions dans un
ordre déterministe propre à ce banc (salage par le digest de Gemma 3), soit
exactement `4 × 2 × 3 = 24` appels.

Tous les éléments — source, candidats, prompt et contrat — sont en anglais et
ASCII. Les répétitions mesurent une stabilité d'ingénierie limitée ; elles ne
constituent pas une estimation générale de fiabilité.

## Transport et contrat

Le transport est Ollama `JSON_ONLY_PROMPTED`, identique au banc Qwen : chaque
appel utilise `think=false`, `stream=false`, température 0, `num_predict=2048`
et `num_ctx=32768`. Aucune relance, réparation, continuation ou lecture du
canal `thinking` comme verdict. La compatibilité du payload exact avec
`gemma3:27b` (acceptation de `think=false`, canal `thinking` absent,
`done_reason=stop`) a été vérifiée avant gel par un smoke sans fixture, hors
qualification.

Le prompt et le modèle `JudgeVerdict` complet restent ceux du banc Qwen. Le
JSON Schema filaire n'est pas transmis au décodeur ; la réponse finale est
validée par Pydantic et toutes ses références doivent être résolues.

## Précondition GPU avant verrou

Avant d'acquérir le verrou et avant tout appel de fixture, le runner lit
`/api/ps`. Le modèle gelé doit être déjà chargé au contexte 32K et présenter
le digest exact ci-dessus, `size > 0` et `size_vram == size`. Si cette
précondition échoue, le runner s'arrête **sans créer de verrou**, de run ou de
requête de fixture. La même égalité est revérifiée après le vingt-quatrième
appel. Le chargement préalable peut être réalisé par un smoke séparé, sans
aucune fixture du banc ; son résultat ne participe pas à la qualification.

## Règle de décision

Gemma 3 est `QUALIFIED_FOR_V10_DESIGN` seulement si les 24 appels :

- reçoivent HTTP 200, une réponse finale non vide, `thinking` vide et
  `done_reason=stop` ;
- produisent un JSON strict valide selon le contrat complet ;
- donnent tous la préférence attendue, dans les deux orientations.

Tout autre résultat est `NOT_QUALIFIED_FOR_V10_DESIGN`. Cette règle stricte ne
rejette pas le modèle en général : elle interdit seulement de le promouvoir
comme juge V10 sur la foi de ce banc — et, par la règle méta, elle active
alors la bascule pré-écrite. Les résultats bruts restent des données de
développement et ne peuvent être recyclés en Q-2 confirmatoire.

## Artefacts et arrêt

Le runner vérifie le digest avant et après les appels, acquiert un verrou
exclusif, archive chaque payload/réponse, écrit un journal JSONL append-only
et un résumé canonique sous `data/runs/`. Les répertoires de corpus ne sont
jamais ouverts. Une interruption après verrou consomme ce banc — c'est le
banc A : une nouvelle tentative n'existe pas sous la règle méta.

La commande publiée est :

```powershell
.\.venv\Scripts\python.exe -m scripts.p7_gemma3_admission --timeout 600
```
