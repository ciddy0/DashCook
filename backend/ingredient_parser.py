import re
from fractions import Fraction

from schemas import Ingredient

_unicode_fractions: dict[str, float] = {
    "½": 0.5,
    "¼": 0.25,
    "¾": 0.75,
    "⅓": 1 / 3,
    "⅔": 2 / 3,
    "⅛": 0.125,
    "⅜": 0.375,
    "⅝": 0.625,
    "⅞": 0.875,
    "⅙": 1 / 6,
    "⅚": 5 / 6,
    "⅕": 0.2,
    "⅖": 0.4,
    "⅗": 0.6,
    "⅘": 0.8,
}

_word_numbers: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}

_UNITS: dict[str, str] = {
    "cups": "cup", "cup": "cup", "c.": "cup",
    "tablespoons": "tablespoon", "tablespoon": "tablespoon",
    "tbsp": "tablespoon", "Tbsp": "tablespoon", "T": "tablespoon",
    "teaspoons": "teaspoon", "teaspoon": "teaspoon", "tsp": "teaspoon",
    "pounds": "pound", "pound": "pound", "lb": "pound", "lb.": "pound", "lbs": "pound", "lbs.": "pound",
    "ounces": "ounce", "ounce": "ounce", "oz": "ounce", "oz.": "ounce",
    "grams": "gram", "gram": "gram", "g": "gram",
    "kilograms": "kilogram", "kilogram": "kilogram", "kg": "kilogram",
    "liters": "liter", "liter": "liter", "litre": "liter", "litres": "liter", "l": "liter", "L": "liter",
    "milliliters": "milliliter", "milliliter": "milliliter",
    "ml": "milliliter", "mL": "milliliter",
    "quarts": "quart", "quart": "quart", "qt": "quart",
    "inches": "inch", "inch": "inch", "in": "inch",
    "sprigs": "sprig", "sprig": "sprig",
    "bunches": "bunch", "bunch": "bunch",
}

_NON_SCALABLE_PHRASES: set[str] = {
    "to taste", "as needed", "for garnish", "optional", "for serving", "to serve",
}

# Words that signal the comma-separated tail is a prep instruction, not a qualifier.
# Only strip after a comma if the first word of the tail is in this set.
_PREP_VERBS: set[str] = {
    "peeled", "chopped", "diced", "sliced", "minced", "grated", "crushed",
    "melted", "softened", "beaten", "crumbled", "shredded", "halved",
    "quartered", "trimmed", "seeded", "deveined", "rinsed", "drained",
    "cooked", "thawed", "packed", "sifted", "divided", "separated",
    "whisked", "zested", "juiced", "roughly", "finely", "thinly", "coarsely",
}

# Unit-like container/count words that follow a quantity but are not real units.
# These are stripped from the name since they carry no ingredient info
# (e.g. "2 cloves garlic" → name="garlic", "1 can tomatoes" → name="tomatoes").
_COUNTABLE_WORDS: set[str] = {
    "clove", "cloves",
    "can", "cans",
    "head", "heads",
    "pinch", "pinches",
    "dash", "dashes",
}

# Words used in "a <word> of X" or "<word> of X" patterns (indefinite amounts)
_INDEFINITE_AMOUNTS: set[str] = {
    "pinch", "dash", "handful", "bit", "drop", "splash", "drizzle",
}


def _parse_number(token: str) -> float | None:
    """Convert a single token to float."""
    try:
        return float(token)
    except ValueError:
        pass
    if "/" in token:
        try:
            return float(Fraction(token))
        except (ValueError, ZeroDivisionError):
            pass
    if token in _unicode_fractions:
        return _unicode_fractions[token]
    if token.lower() in _word_numbers:
        return float(_word_numbers[token.lower()])
    return None


def _parse_quantity(tokens: list[str]) -> tuple[float | None, float | None, int]:
    """
    Returns (quantity, quantity_max, tokens_consumed).
    Handles single numbers, mixed numbers, unicode mixed numbers, and ranges.
    """
    if not tokens:
        return None, None, 0

    first = tokens[0]

    # check for token like "2½" — integer followed by unicode fraction
    for uf, val in _unicode_fractions.items():
        if uf in first:
            parts = first.split(uf)
            whole_str = parts[0]
            if whole_str == "":
                return val, None, 1
            try:
                whole = float(whole_str)
                return whole + val, None, 1
            except ValueError:
                pass

    # range: "1-2" — split on hyphen when both sides are numeric
    if "-" in first and not first.startswith("-"):
        parts = first.split("-", 1)
        lo = _parse_number(parts[0])
        hi = _parse_number(parts[1])
        if lo is not None and hi is not None:
            return lo, hi, 1

    first_num = _parse_number(first)
    if first_num is None:
        return None, None, 0

    # try spaced range: "5 - 6"
    if len(tokens) >= 3 and tokens[1] == "-":
        hi = _parse_number(tokens[2])
        if hi is not None:
            return first_num, hi, 3

    # try mixed number: integer followed by fraction token
    if len(tokens) >= 2:
        second_num = _parse_number(tokens[1])
        if second_num is not None and second_num < 1:
            return first_num + second_num, None, 2

    return first_num, None, 1


def _extract_paren_notes(raw: str) -> list[str]:
    """
    Extract meaningful content from all parenthetical groups using stack-based
    parsing to handle nesting. Filters out 'Note N' references.
    """
    # Collect top-level paren groups
    depth = 0
    groups: list[str] = []
    current: list[str] = []

    for ch in raw:
        if ch == "(":
            if depth > 0:
                current.append(ch)
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                groups.append("".join(current))
                current = []
            elif depth > 0:
                current.append(ch)
        elif depth > 0:
            current.append(ch)

    notes: list[str] = []
    for group in groups:
        # Split outer content from inner parens
        inner_contents = re.findall(r"\(([^()]*)\)", group)
        outer = re.sub(r"\([^()]*\)", "", group).lstrip(",").strip()

        for part in [outer] + inner_contents:
            part = part.strip().lstrip(",").strip()
            if not part:
                continue
            # Skip "Note N" references and "see note(s)" / "*see note" annotations
            if re.match(r"^note\s*\d*", part, re.IGNORECASE):
                continue
            if re.match(r"^\*?see\s+notes?", part, re.IGNORECASE):
                continue
            # Skip bare asterisk-prefixed annotations
            if part.startswith("*"):
                continue
            notes.append(part)

    return notes


def _strip_parens(text: str) -> str:
    """Remove all parenthetical groups from text, respecting nesting depth."""
    result = []
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth > 0:
                depth -= 1
        elif depth == 0:
            result.append(ch)
    return "".join(result)


def parse_ingredient(raw: str) -> Ingredient:
    """Parse a raw ingredient string into a structured Ingredient."""
    lower = raw.lower()
    scalable = not any(phrase in lower for phrase in _NON_SCALABLE_PHRASES)

    paren_notes = _extract_paren_notes(raw)

    # strip all parentheticals for the main quantity/unit/name parse
    stripped = _strip_parens(raw)
    stripped = re.sub(r"\s+", " ", stripped).strip()   # normalize whitespace
    stripped = stripped.strip(",").strip()              # strip leading/trailing commas
    stripped = stripped.replace("*", "")               # strip annotation markers

    # split concatenated qty+unit: "150g" → "150 g", "1.5kg" → "1.5 kg"
    stripped = re.sub(r'(?<![a-zA-Z])(\d+(?:\.\d+)?)(kg|ml|mL|g|oz|lb)\b', r'\1 \2', stripped)

    tokens = stripped.split()
    quantity, quantity_max, consumed = _parse_quantity(tokens)
    tokens = tokens[consumed:]

    # check for unit
    unit: str | None = None
    if tokens:
        unit_token = tokens[0]
        if unit_token in _UNITS:
            unit = _UNITS[unit_token]
            tokens = tokens[1:]
        elif unit_token.lower() in _UNITS:
            unit = _UNITS[unit_token.lower()]
            tokens = tokens[1:]

    # skip alternative measurement: "/ 3 tbsp" or "/ 1.5 oz" after primary qty+unit
    if tokens and tokens[0] == "/" and quantity is not None:
        tokens = tokens[1:]  # skip "/"
        _, _, alt_consumed = _parse_quantity(tokens)
        if alt_consumed > 0:
            tokens = tokens[alt_consumed:]
            if tokens:
                alt_unit = tokens[0]
                if alt_unit in _UNITS or alt_unit.lower() in _UNITS:
                    tokens = tokens[1:]

    # skip unit-like container words (e.g. "cloves", "bunch", "can") when a quantity was parsed
    # only when there are more tokens — don't strip if it would leave the name empty
    if tokens and unit is None and quantity is not None:
        check = tokens[0].lower().rstrip(",")
        if check in _COUNTABLE_WORDS and len(tokens) > 1:
            tokens = tokens[1:]

    # strip leading "of" connector (e.g. "8 tablespoons of butter" → "butter")
    if tokens and tokens[0].lower() == "of":
        tokens = tokens[1:]

    name = " ".join(tokens).strip()

    # if nothing was parsed as quantity (e.g. "juice of 1 lemon"), use full stripped string as name
    if quantity is None and not unit:
        name = stripped

    # strip inline prep notes after comma only when the tail starts with a prep verb
    # (e.g. "carrots, peeled and diced" → "carrots", but "beef stock, low sodium" stays)
    if "," in name:
        tail = name.split(",", 1)[1].strip().lower()
        first_word = tail.split()[0].rstrip(",") if tail.split() else ""
        if first_word in _PREP_VERBS:
            name = name.split(",")[0].strip()

    # handle indefinite amounts: "a pinch of X", "dash of X" → name = X
    if quantity is None and not unit:
        m = re.match(r'^(?:a\s+|an\s+)?(\w+)\s+of\s+(.+)$', name, re.IGNORECASE)
        if m and m.group(1).lower() in _INDEFINITE_AMOUNTS:
            name = m.group(2)

    # handle reversed format: "Thai basil, 3 - 5 sprigs" → name="Thai basil", qty=3, qty_max=5, unit="sprig"
    if quantity is None and not unit:
        rev = re.search(r',?\s+(\d+(?:[./]\d+)?)\s*(?:-\s*(\d+(?:[./]\d+)?)\s+)?(\w+)$', name)
        if rev:
            unit_candidate = rev.group(3)
            if unit_candidate in _UNITS or unit_candidate.lower() in _UNITS:
                name = name[:rev.start()].strip()
                quantity = float(rev.group(1))
                quantity_max = float(rev.group(2)) if rev.group(2) else None
                unit = _UNITS.get(unit_candidate) or _UNITS.get(unit_candidate.lower())

    # re-append cleaned parenthetical content as "(note)"
    if paren_notes:
        name = name + " " + " ".join(f"({n})" for n in paren_notes)

    return Ingredient(
        raw=raw,
        name=name,
        quantity=quantity,
        quantity_max=quantity_max,
        unit=unit,
        scalable=scalable,
    )


# Matches "1.5 tsp each salt and pepper" → splits into two ingredients
_EACH_AND_PATTERN = re.compile(
    r"^([\d./½¼¾⅓⅔⅛⅜⅝⅞⅙⅚⅕⅖⅗⅘]+(?:\s+[\d./½¼¾⅓⅔⅛⅜⅝⅞⅙⅚⅕⅖⅗⅘]+)?)"
    r"\s+(\w+)"
    r"\s+each\s+"
    r"(.+?)\s+and\s+(.+)$",
    re.IGNORECASE,
)


def parse_ingredients(raw: str) -> list[Ingredient]:
    """
    Parse a raw ingredient string into one or more Ingredient objects.
    Handles 'N unit each X and Y' by splitting into two separate ingredients.
    """
    m = _EACH_AND_PATTERN.match(raw.strip())
    if m:
        qty_str, unit_str, x, y = m.group(1), m.group(2), m.group(3), m.group(4)
        return [
            parse_ingredient(f"{qty_str} {unit_str} {x}"),
            parse_ingredient(f"{qty_str} {unit_str} {y}"),
        ]
    return [parse_ingredient(raw)]
