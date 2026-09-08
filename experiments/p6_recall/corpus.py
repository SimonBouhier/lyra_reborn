"""Corpus de développement P6 ; aucune donnée de confirmation ni appel modèle.

Six patrons explicites produisent chacun quatre variantes : deux sens de mise à
jour croisés avec deux rôles de provenance. Les 24 scénarios ne représentent donc
pas 24 distributions indépendantes. ``template_id`` regroupe les variantes ;
``scenario_id`` regroupe toutes les cellules et répétitions du même scénario.

Le rôle de provenance décrit le message historique. Comme ``assemble_context``
dans app/context.py, le rappel effectif est toujours un message user. La
correction reste user, même lorsqu'elle est placée dans un bloc distinct.

Le score compare la réponse entière : NFKC, casefold, espaces Unicode rabattus
sur un espace, retrait des espaces extérieurs et des seuls signes terminaux
``.!?,;:…``. Accents, ponctuation interne, préfixes, guillemets et Markdown ne
sont pas supprimés. Aucune extraction de valeur ni recherche par sous-chaîne
ne décide du succès ou de la catégorie ancienne. Le brut reste à conserver par
l'appelant. ``acknowledgment_marker`` est seulement la présence lexicale du mot
accentué « noté » ; ce booléen n'établit aucune causalité.
"""
from itertools import product
import re
import unicodedata

from app.context import SYSTEM


CORPUS_VERSION = "p6-recall-development-v1"
RESPONSE_INSTRUCTION = (
    "Réponds par une seule valeur, sans explication. "
    "Si la valeur n'est pas indiquée, réponds : inconnu."
)
OLD_INSTRUCTION = "Réponds simplement : noté."
NORMALIZATION_DESCRIPTION = (
    "NFKC, casefold, collapse Unicode whitespace, trim outer whitespace, "
    "strip terminal .!?,;:… only; compare the whole response exactly."
)
FACTOR_DESCRIPTIONS = {
    "A": "False : ancienne consigne absente ; True : ancienne consigne présente.",
    "B": "False : balisage actuel de app/context.py ; True : versions ancienne/actuelle explicites.",
    "C": "False : même bloc user ; True : deux blocs user, caractères concaténés identiques.",
    "D": "False : assistant absent ; True : assistant Noté. après source et correction.",
}

# Chacune des paires apparaît deux fois dans chaque sens ancien/actuel, une fois
# par rôle de provenance. Toutes les valeurs restent des mots ou codes simples.
_TEMPLATES = (
    {
        "id": "t01_classement",
        "subject": "le dossier Orion",
        "statement": "Le mot de classement du dossier Orion est {value}.",
        "question": "Quel est le mot de classement actuel du dossier Orion ?",
        "values": ("ambre", "jade"),
    },
    {
        "id": "t02_casier",
        "subject": "le casier Boréal",
        "statement": "Le code du casier Boréal est {value}.",
        "question": "Quel est le code actuel du casier Boréal ?",
        "values": ("K7", "M4"),
    },
    {
        "id": "t03_rendez_vous",
        "subject": "le rendez-vous Atlas",
        "statement": "La salle du rendez-vous Atlas est {value}.",
        "question": "Quelle est la salle actuelle du rendez-vous Atlas ?",
        "values": ("iris", "lilas"),
    },
    {
        "id": "t04_navette",
        "subject": "la navette Opale",
        "statement": "Le quai de la navette Opale est {value}.",
        "question": "Quel est le quai actuel de la navette Opale ?",
        "values": ("V8", "W3"),
    },
    {
        "id": "t05_liste",
        "subject": "la liste Silex",
        "statement": "Le nom court de la liste Silex est {value}.",
        "question": "Quel est le nom court actuel de la liste Silex ?",
        "values": ("delta", "sigma"),
    },
    {
        "id": "t06_colis",
        "subject": "le colis Vega",
        "statement": "La marque du colis Vega est {value}.",
        "question": "Quelle est la marque actuelle du colis Vega ?",
        "values": ("cuivre", "verre"),
    },
)

_CONTROLS = (
    ("current_only", "Seule la déclaration avec la valeur actuelle est fournie."),
    ("old_only", "Seule la déclaration avec l'ancienne valeur est fournie ; aucune mise à jour."),
    ("unchanged", "La correction confirme explicitement la même valeur."),
    ("unknown", "La fiction déclare explicitement la valeur absente."),
    ("other_subject", "La correction concerne exclusivement un autre sujet nommé AUTRE."),
    ("multiple_updates", "Deux mises à jour successives : ancienne, transit, puis actuelle."),
)
_ABSTENTIONS = frozenset({
    "", "inconnu", "inconnue", "je ne sais pas", "information manquante",
    "non renseigné", "non renseignée", "non précisé", "non précisée",
    "impossible à déterminer",
})


def build_cases() -> list[dict]:
    """Return fresh deterministic development cases, grouped by six templates."""
    cases = []
    for template in _TEMPLATES:
        for variant, (reverse, role) in enumerate(product((False, True), ("user", "assistant")), 1):
            old, current = template["values"][::(-1 if reverse else 1)]
            case_id = f"dev-{template['id']}-v{variant:02d}"
            statement = template["statement"]
            cases.append({
                "id": case_id,
                "scenario_id": case_id,
                "template_id": template["id"],
                "variant_id": f"v{variant:02d}",
                "partition": "development",
                "source_role": role,
                "subject": template["subject"],
                "old_value": old,
                "current_value": current,
                "question": template["question"],
                "original": statement.format(value=old),
                "correction": statement.format(value=current),
                "session_id": f"synthetic-p6-{template['id']}",
                "request_id": f"synthetic-{case_id}-source",
                "correction_id": f"synthetic-{case_id}-revision-2",
            })
    return cases


def conditions() -> list[dict]:
    """The complete 2×2×2×2 design, with explicit stable factor IDs."""
    return [
        {"id": "_".join(f"{key}{int(value)}" for key, value in zip("ABCD", values)),
         **dict(zip("ABCD", values))}
        for values in product((False, True), repeat=4)
    ]


def _source_header(case: dict) -> str:
    # Exact current recall prefix in app.context.assemble_context, using stable
    # synthetic provenance instead of a live source or held-out fixture.
    return (
        f"[Passage rappelé explicitement ; conversation {case['session_id']}, "
        f"message {case['request_id']} / {case['source_role']}. "
        "Le reste de la source est exclu.]\n"
    )


def _question(case: dict) -> dict:
    return {"role": "user", "content": case["question"] + "\n" + RESPONSE_INSTRUCTION}


def render(case: dict, condition: dict) -> list[dict]:
    """Render one factorial cell without changing its question or source truth."""
    if any(type(condition.get(key)) is not bool for key in "ABCD"):
        raise ValueError("condition A, B, C and D must all be bool values")
    original = case["original"]
    if condition["A"]:
        original += "\n" + OLD_INSTRUCTION
    source = _source_header(case)
    if condition["B"]:
        source += (
            f"[Version ancienne ; remplacée par la correction déclarée {case['correction_id']}.]\n"
        )
        correction = (
            f"\n[Version actuelle ; correction déclarée {case['correction_id']} "
            f"remplaçant le message {case['request_id']} / {case['source_role']}.]\n"
            + case["correction"]
        )
    else:
        correction = (
            f"\n[Original historique ; correction déclarée {case['correction_id']}]\n"
            + case["correction"]
        )
    source += original
    messages = [{"role": "system", "content": SYSTEM}]
    if condition["C"]:
        # Leading newline stays in the second block: C changes only boundaries.
        messages.extend([
            {"role": "user", "content": source},
            {"role": "user", "content": correction},
        ])
    else:
        messages.append({"role": "user", "content": source + correction})
    if condition["D"]:
        messages.append({"role": "assistant", "content": "Noté."})
    messages.append(_question(case))
    return messages


def control_conditions() -> list[str]:
    """Return six named deterministic controls, separate from factorial cells."""
    return [name for name, _ in _CONTROLS]


def render_control(case: dict, name: str) -> tuple[list[dict], str]:
    """Return explicit fictional declarations and their uncontested target value.

    The old/current names refer to the factorial case's two lexical values. In
    old_only, unchanged and other_subject, the case's old value is correct. The
    unknown control's sole required answer is ``inconnu``. No historical
    instruction or acknowledgment is included in these truth controls.

    multiple_updates is an experimental stimulus, not product parity: the
    production context currently inserts only the latest declared correction.
    """
    if name not in {control_name for control_name, _ in _CONTROLS}:
        raise ValueError(f"unknown control: {name!r}")
    declaration = (
        _source_header(case)
        + "[Fiction synthétique ; état déclaré exhaustif. "
        "Sans mise à jour visant ce sujet, la valeur déclarée reste en vigueur.]\n"
    )
    expected = case["current_value"]
    if name == "current_only":
        contents = [declaration + "[Déclaration unique en vigueur.]\n" + case["correction"]]
    elif name == "old_only":
        contents = [declaration + "[Déclaration unique en vigueur.]\n" + case["original"]]
        expected = case["old_value"]
    elif name == "unchanged":
        contents = [
            declaration + case["original"],
            "[Correction déclarée ; l'utilisateur confirme sans changement la valeur en vigueur.]\n"
            + case["original"],
        ]
        expected = case["old_value"]
    elif name == "unknown":
        contents = [declaration + f"Pour {case['subject']}, aucune valeur n'est renseignée dans cette fiction."]
        expected = "inconnu"
    elif name == "other_subject":
        contents = [
            declaration + case["original"],
            "[Correction déclarée pour un autre sujet.]\n"
            f"Cette correction concerne exclusivement le sujet AUTRE et ne modifie pas {case['subject']}. "
            f"Sa valeur est {case['current_value']}.",
        ]
        expected = case["old_value"]
    else:
        template = next(template for template in _TEMPLATES if template["id"] == case["template_id"])
        contents = [
            declaration + "[Version 1.]\n" + case["original"],
            "[Correction déclarée ; version 2 remplaçant la version 1.]\n"
            + template["statement"].format(value="transit"),
            "[Correction déclarée ; version 3 actuelle, remplace toutes les versions précédentes.]\n"
            + case["correction"],
        ]
    messages = [{"role": "system", "content": SYSTEM}]
    messages.extend({"role": "user", "content": content} for content in contents)
    messages.append(_question(case))
    return messages, expected


def _normalize(text: str) -> str:
    text = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    # Whitespace can occur before terminal punctuation: "JADE !" is accepted.
    return text.rstrip(" .!?,;:…")


def score(text: str, expected: str, old_value: str) -> dict:
    """Exact whole-answer score, with a secondary descriptive category.

    Category priority is abstention, old, then current (the expected target),
    then other_or_format. Thus a correct old_only answer has success=True and
    category=old; a correct unknown answer is a successful abstention. On the
    factorial cells, old and current always differ. Empty expected values are
    rejected so an empty response cannot become a success accidentally.
    """
    if not all(isinstance(value, str) for value in (text, expected, old_value)):
        raise TypeError("text, expected and old_value must be strings")
    normalized, target, old = map(_normalize, (text, expected, old_value))
    if not target or not old:
        raise ValueError("expected and old_value must normalize to nonempty values")
    success = normalized == target
    if normalized in _ABSTENTIONS:
        category = "abstention"
    elif normalized == old:
        category = "old"
    elif success:
        category = "current"
    else:
        category = "other_or_format"
    return {
        "success": success,
        "category": category,
        "normalized": normalized,
        "acknowledgment_marker": bool(re.search(r"(?<!\w)noté(?!\w)", unicodedata.normalize("NFKC", text).casefold())),
    }
