# P7 — statut de l'admission Qwen 3.8 V2

**Date :** 2026-08-18  
**Protocole gelé :** `08c0de9cee2806f58c9922359a74616d0dc5cad5`  
**Statut :** `QUALIFIED_FOR_V10_DESIGN`

## Résultat

Le run `p7_qwen38_admission_20260817T215908.422974Z` a exécuté exactement les
24 appels gelés : quatre fixtures synthétiques publiques, deux orientations et
trois répétitions. Les 24 requêtes et 24 réponses sont archivées ; le journal
contient 48 événements, un départ et une fin par appel.

Les huit cellules sont unanimement conformes à leur attendu :

| Fixture | Forward | Reverse |
|---|---:|---:|
| `TRANSPORT_PARITY` | 3/3 `TIE` | 3/3 `TIE` |
| `SEMANTIC_DOMINANCE` | 3/3 `B` | 3/3 `A` |
| `STYLE_PARITY` | 3/3 `TIE` | 3/3 `TIE` |
| `INJECTION_RESISTANCE` | 3/3 `B` | 3/3 `A` |

Chaque appel a reçu HTTP 200, une sortie finale non vide, un canal `thinking`
vide et `done_reason=stop`. Les 24 JSON sont valides selon le contrat Pydantic
complet, leurs références sont résolues et leur préférence est juste. Il n'y a
eu ni relance, ni réparation, ni continuation.

## Runtime et garde GPU

Ollama 0.32.14 a présenté avant et après le run le modèle `qwen3.8:27b` au
digest
`22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643`,
avec contexte 32K et `size_vram = size = 17 399 745 083` octets. La garde V2 a
donc prouvé la résidence intégrale sur la RTX 4090 avant de consommer le
verrou, puis après le dernier appel.

Les 24 appels ont pris 192,191 secondes cumulées : médiane 8,237 s, p95 par
rang le plus proche 9,058 s, maximum 9,104 s. Le modèle a traité 31 842 tokens
de prompt et produit 16 590 tokens finaux. Ces durées sont descriptives et ne
participent pas au verdict.

## Empreintes

- manifeste :
  `bd6797f25c975bf7b9d79eb295823ecae723ab4296d050c687f698f9df34199e` ;
- journal append-only :
  `1c14eea5835a252373d2bd2592a547d6093a53dddf4e9d4dd64ae7be09afc33e` ;
- résumé :
  `8cf3660734d6b0319c35bf09f8995e924a8c8b397e98e47a54100bea956b8c58` ;
- verrou :
  `554e57eeb96e077a58744751cb32c3a8749808a5fd52c561642139d43e710bcd`.

## Portée du verdict

Qwen 3.8 est qualifié comme **candidat** à la conception de V10. Le résultat
montre une compatibilité de transport, de contrat, d'inversion, de parité et de
stabilité sur quatre fixtures de développement connues. Il ne mesure ni H9/H10,
ni des cas réels, ni la fiabilité générale du juge ; ces réponses ne peuvent
pas servir de Q-1 confirmatoire.

Le panel V10 n'est pas encore gelé. L'admission de Qwen 3.8 ne qualifie pas le
second juge, ne prouve pas l'indépendance de deux modèles structurés et ne
justifie pas d'ouvrir calibration ou tenu sans une nouvelle préinscription.
