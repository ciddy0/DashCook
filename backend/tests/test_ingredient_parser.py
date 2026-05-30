import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.ingredient_parser import parse_ingredient, parse_ingredients


def test_basic_cup():
    ing = parse_ingredient("2 cups flour")
    assert ing.quantity == 2.0
    assert ing.unit == "cup"
    assert ing.name == "flour"
    assert ing.scalable is True


def test_slash_fraction():
    ing = parse_ingredient("1/2 teaspoon salt")
    assert ing.quantity == 0.5
    assert ing.unit == "teaspoon"


def test_mixed_number():
    ing = parse_ingredient("2 1/2 cups beef broth")
    assert ing.quantity == 2.5
    assert ing.unit == "cup"


def test_unicode_mixed():
    ing = parse_ingredient("2½ cups milk")
    assert ing.quantity == 2.5
    assert ing.unit == "cup"


def test_range():
    ing = parse_ingredient("1-2 tablespoons oil")
    assert ing.quantity == 1.0
    assert ing.quantity_max == 2.0
    assert ing.unit == "tablespoon"


def test_parenthetical():
    ing = parse_ingredient("3 (14 oz) cans tomatoes")
    assert ing.quantity == 3.0
    assert ing.unit is None
    assert ing.name == "tomatoes (14 oz)"


def test_to_taste():
    ing = parse_ingredient("salt and pepper, to taste")
    assert ing.scalable is False
    assert ing.quantity is None


def test_word_number():
    ing = parse_ingredient("one large egg")
    assert ing.quantity == 1.0
    assert ing.unit is None
    assert ing.name == "large egg"


def test_mid_string_quantity():
    ing = parse_ingredient("juice of 1 lemon")
    assert ing.quantity is None
    assert ing.name == "juice of 1 lemon"


def test_for_garnish():
    ing = parse_ingredient("for garnish")
    assert ing.scalable is False


def test_raw_preserved():
    raw = "2 cups flour"
    ing = parse_ingredient(raw)
    assert ing.raw == raw


def test_unicode_fraction_only():
    ing = parse_ingredient("½ cup sugar")
    assert ing.quantity == 0.5
    assert ing.unit == "cup"
    assert ing.name == "sugar"


def test_spaced_range():
    ing = parse_ingredient("5 - 6 beef short ribs (, 300-400g/10-14oz each (Note 1))")
    assert ing.quantity == 5.0
    assert ing.quantity_max == 6.0
    assert ing.name.startswith("beef short ribs")


def test_capitalized_unit():
    ing = parse_ingredient("3 Tablespoons olive oil")
    assert ing.quantity == 3.0
    assert ing.unit == "tablespoon"
    assert ing.name == "olive oil"


def test_double_parens():
    ing = parse_ingredient("1 cup dry red wine ((such as Cote du Rhone or Pinot Noir))")
    assert ing.quantity == 1.0
    assert ing.unit == "cup"
    assert ing.name == "dry red wine (such as Cote du Rhone or Pinot Noir)"


def test_paren_prep_note():
    ing = parse_ingredient("1 yellow onion (, diced)")
    assert ing.quantity == 1.0
    assert ing.name == "yellow onion (diced)"


def test_sprigs_unit():
    ing = parse_ingredient("2 sprigs fresh thyme")
    assert ing.quantity == 2.0
    assert ing.unit == "sprig"
    assert ing.name == "fresh thyme"


def test_cloves_garlic():
    ing = parse_ingredient("2 cloves garlic")
    assert ing.quantity == 2.0
    assert ing.unit is None
    assert ing.name == "garlic"


def test_pinch_of_salt():
    ing = parse_ingredient("a pinch of salt")
    assert ing.quantity is None
    assert ing.unit is None
    assert ing.name == "salt"


def test_bunch_cilantro():
    ing = parse_ingredient("1 bunch cilantro")
    assert ing.quantity == 1.0
    assert ing.unit == "bunch"
    assert ing.name == "cilantro"


def test_bunch_fresh_cilantro_with_prep():
    ing = parse_ingredient("1 bunch fresh cilantro (, chopped)")
    assert ing.quantity == 1.0
    assert ing.unit == "bunch"
    assert ing.name == "fresh cilantro (chopped)"


def test_bunch_thai_basil():
    ing = parse_ingredient("1 bunch Thai basil leaves")
    assert ing.quantity == 1.0
    assert ing.unit == "bunch"
    assert ing.name == "Thai basil leaves"


def test_can_with_parenthetical():
    ing = parse_ingredient("1 can (14 oz) diced tomatoes")
    assert ing.quantity == 1.0
    assert ing.unit is None
    assert ing.name == "diced tomatoes (14 oz)"


def test_comma_prep_note():
    ing = parse_ingredient("3 carrots, peeled and diced")
    assert ing.quantity == 3.0
    assert ing.unit is None
    assert ing.name == "carrots"


def test_zest_of_lemon():
    ing = parse_ingredient("zest of 1 lemon")
    assert ing.quantity is None
    assert ing.name == "zest of 1 lemon"


def test_large_eggs():
    ing = parse_ingredient("4 large eggs")
    assert ing.quantity == 4.0
    assert ing.unit is None
    assert ing.name == "large eggs"


def test_dash_of_hot_sauce():
    ing = parse_ingredient("dash of hot sauce")
    assert ing.quantity is None
    assert ing.unit is None
    assert ing.name == "hot sauce"


def test_optional_scalable():
    ing = parse_ingredient("1/4 tsp black pepper, optional")
    assert ing.scalable is False


def test_comma_softened():
    ing = parse_ingredient("8 oz cream cheese, softened")
    assert ing.quantity == 8.0
    assert ing.unit == "ounce"
    assert ing.name == "cream cheese"


# --- tests for recently fixed bugs ---

def test_note_reference_stripped():
    """(Note N) references should not appear in the name."""
    ing = parse_ingredient("2 cups (500ml) dry red wine ((Note 2))")
    assert "Note" not in ing.name
    assert "note" not in ing.name.lower()
    assert "(500ml)" in ing.name


def test_qualifier_after_comma_kept():
    """Qualifiers like 'low sodium' after a comma should be preserved."""
    ing = parse_ingredient("2 cups (500ml) beef stock/broth, low sodium")
    assert "low sodium" in ing.name


def test_nested_paren_alternatives_kept():
    """Alternatives inside nested parens like '(brown, yellow or white)' should appear in name."""
    ing = parse_ingredient("1 large onion (, chopped (brown, yellow or white))")
    assert ing.quantity == 1.0
    assert "brown, yellow or white" in ing.name


def test_each_and_splits_into_two():
    """'N unit each X and Y' should produce two separate ingredients."""
    ings = parse_ingredients("1.5 tsp each salt and pepper")
    assert len(ings) == 2
    names = {ing.name for ing in ings}
    assert "salt" in names
    assert "pepper" in names
    for ing in ings:
        assert ing.quantity == 1.5
        assert ing.unit == "teaspoon"


def test_of_connector_stripped():
    """'of' between unit and ingredient name should not appear in the name."""
    ing = parse_ingredient("8 tablespoons of salted butter")
    assert ing.quantity == 8.0
    assert ing.unit == "tablespoon"
    assert ing.name == "salted butter"


def test_asterisk_note_stripped():
    """(*see note) and similar asterisk-prefixed paren annotations should not appear in the name."""
    ing = parse_ingredient("36 ounces pasta sauce (*see note)")
    assert ing.quantity == 36.0
    assert ing.unit == "ounce"
    assert ing.name == "pasta sauce"


def test_oz_dot_unit():
    """'oz.' with trailing period should be recognised as ounce."""
    ing = parse_ingredient("40 oz. marinara sauce (see notes)")
    assert ing.quantity == 40.0
    assert ing.unit == "ounce"
    assert ing.name == "marinara sauce"


def test_lb_dot_unit():
    """'lb.' with trailing period should be recognised as pound."""
    ing = parse_ingredient("¾ lb. ground beef")
    assert ing.quantity == 0.75
    assert ing.unit == "pound"
    assert ing.name == "ground beef"


def test_see_notes_stripped():
    """(see notes) / (see note) parentheticals should not appear in the name."""
    ing = parse_ingredient("40 oz. marinara sauce (see notes)")
    assert "see notes" not in ing.name.lower()
    assert "see note" not in ing.name.lower()


# --- pho recipe / metric format fixes ---

def test_concatenated_metric_unit():
    """'150g ginger' should parse qty=150, unit=gram."""
    ing = parse_ingredient("150g ginger")
    assert ing.quantity == 150.0
    assert ing.unit == "gram"
    assert ing.name == "ginger"


def test_concatenated_kg_with_alt():
    """'1.5kg / 3lb beef brisket' — primary metric qty+unit, alt skipped."""
    ing = parse_ingredient("1.5kg / 3lb beef brisket")
    assert ing.quantity == 1.5
    assert ing.unit == "kilogram"
    assert ing.name == "beef brisket"


def test_concatenated_g_with_paren_and_alt():
    """'150g / 5oz ginger (, sliced down the centre)' — qty=150g, paren note kept."""
    ing = parse_ingredient("150g / 5oz ginger (, sliced down the centre)")
    assert ing.quantity == 150.0
    assert ing.unit == "gram"
    assert "ginger" in ing.name
    assert "sliced down the centre" in ing.name


def test_alt_measurement_skipped_ml():
    """'40 ml / 3 tbsp fish sauce ((Note 2))' — alt measurement and Note stripped."""
    ing = parse_ingredient("40 ml / 3 tbsp fish sauce ((Note 2))")
    assert ing.quantity == 40.0
    assert ing.unit == "milliliter"
    assert ing.name == "fish sauce"


def test_british_litres():
    """'3.5 litres / 3.75 quarts water ((15 cups))' — litres recognised, alt skipped."""
    ing = parse_ingredient("3.5 litres / 3.75 quarts water ((15 cups))")
    assert ing.quantity == 3.5
    assert ing.unit == "liter"
    assert "water" in ing.name
    assert "15 cups" in ing.name


def test_cloves_spice_not_stripped_when_sole_token():
    """'3 cloves ((the spice cloves!))' — 'cloves' kept as name when it's the only token."""
    ing = parse_ingredient("3 cloves ((the spice cloves!))")
    assert ing.quantity == 3.0
    assert ing.unit is None
    assert "cloves" in ing.name
    assert not ing.name.startswith(" ")  # no leading space


def test_reversed_name_qty_range_unit():
    """'Thai basil, 3 - 5 sprigs' — name before qty, range, unit at end."""
    ing = parse_ingredient("Thai basil, 3 - 5 sprigs")
    assert ing.quantity == 3.0
    assert ing.quantity_max == 5.0
    assert ing.unit == "sprig"
    assert ing.name == "Thai basil"


def test_reversed_with_slash_name_and_paren():
    """'Coriander/cilantro, 3 - 5 sprigs ((or more basil))' — slash in name, paren kept."""
    ing = parse_ingredient("Coriander/cilantro, 3 - 5 sprigs ((or more basil))")
    assert ing.quantity == 3.0
    assert ing.quantity_max == 5.0
    assert ing.unit == "sprig"
    assert "Coriander/cilantro" in ing.name
    assert "or more basil" in ing.name


def test_concatenated_g_with_alt_and_prep_note():
    """'30g / 1 oz beef tenderloin, raw, very thinly sliced' — thinly sliced kept in name."""
    ing = parse_ingredient("30g / 1 oz beef tenderloin, raw, very thinly sliced ((Note 4))")
    assert ing.quantity == 30.0
    assert ing.unit == "gram"
    assert "beef tenderloin" in ing.name
    assert "thinly sliced" in ing.name


def test_asterisk_annotation_stripped():
    """Trailing '*' annotation markers should be removed from names."""
    ing = parse_ingredient("Hoisin sauce*")
    assert ing.name == "Hoisin sauce"
    assert "*" not in ing.name


def test_asterisk_before_paren():
    """'Sriracha* ((for spiciness))' — asterisk stripped, paren note kept."""
    ing = parse_ingredient("Sriracha* ((for spiciness))")
    assert ing.name == "Sriracha (for spiciness)"
    assert "*" not in ing.name


def test_and_fraction_mixed_number():
    """'1 and 1/2 cups cold whole milk' — 'and' between integer and fraction is a mixed number."""
    ing = parse_ingredient("1 and 1/2 cups (360ml) cold whole milk")
    assert ing.quantity == 1.5
    assert ing.unit == "cup"
    assert "cold whole milk" in ing.name
    assert "360ml" in ing.name
    assert "and" not in ing.name.split("(")[0]


def test_and_fraction_butter():
    """'1 and 1/2 cups unsalted butter, softened to room temperature' — mixed number + state kept."""
    ing = parse_ingredient("1 and 1/2 cups (340g) unsalted butter, softened to room temperature")
    assert ing.quantity == 1.5
    assert ing.unit == "cup"
    assert "unsalted butter" in ing.name
    assert "softened to room temperature" in ing.name
    assert "340g" in ing.name


def test_softened_to_room_temperature_kept():
    """Prep phrase with extra context like 'to room temperature' should stay in name."""
    ing = parse_ingredient("1/4 cup (4 Tbsp; 56g) unsalted butter, softened to room temperature")
    assert ing.quantity == 0.25
    assert ing.unit == "cup"
    assert "unsalted butter" in ing.name
    assert "softened to room temperature" in ing.name


def test_softened_alone_stripped():
    """Plain 'softened' after comma (no extra context) should still be stripped."""
    ing = parse_ingredient("8 oz cream cheese, softened")
    assert ing.quantity == 8.0
    assert ing.unit == "ounce"
    assert ing.name == "cream cheese"


def test_nested_paren_no_duplication():
    """'1kg / 2lb marrow bones ((leg, knuckle), cut to reveal marrow)' — no repeated text."""
    ing = parse_ingredient("1kg / 2lb marrow bones ((leg, knuckle), cut to reveal marrow)")
    assert ing.quantity == 1.0
    assert ing.unit == "kilogram"
    assert "marrow bones" in ing.name
    # "cut to reveal marrow" should appear at most once
    assert ing.name.count("cut to reveal marrow") <= 1


def test_nested_paren_no_trailing_comma_in_note():
    """Paren content with inner sub-paren should not have trailing comma in outer note."""
    # "or natural rock salt (for salt water)" should not become "or natural rock salt ,"
    ing = parse_ingredient(
        "1.5 cups Korean coarse sea salt (or natural rock salt (for salt water), (285g / 10 ounces))"
    )
    assert ing.quantity == 1.5
    assert ing.unit == "cup"
    assert "Korean coarse sea salt" in ing.name
    # no trailing comma inside parenthetical notes
    assert " ," not in ing.name
    assert ",)" not in ing.name


def test_nested_paren_no_trailing_comma_cooking_salt():
    """Cooking salt with inner sub-paren note should not produce trailing comma."""
    ing = parse_ingredient(
        "1/2 cup cooking salt (, medium sized crystals (for sprinkle), (97g / 3.4 ounces))"
    )
    assert ing.quantity == 0.5
    assert ing.unit == "cup"
    assert "cooking salt" in ing.name
    assert " ," not in ing.name
    assert ",)" not in ing.name


# --- compound quantity tests ---

def test_compound_qty_spaced_plus():
    """'1/4 cup + 1 tablespoon cocoa powder (30g)' → two ingredients sharing the name."""
    ings = parse_ingredients("1/4 cup +1 tablespoon Dutch-process cocoa powder (30g)")
    assert len(ings) == 2
    assert ings[0].quantity == 0.25
    assert ings[0].unit == "cup"
    assert ings[1].quantity == 1.0
    assert ings[1].unit == "tablespoon"
    for ing in ings:
        assert "Dutch-process cocoa powder" in ing.name
        assert "30g" in ing.name


def test_compound_qty_concatenated_plus():
    """'1/4 cup+1 tablespoon black cocoa powder (30g)' → two ingredients."""
    ings = parse_ingredients("1/4 cup+1 tablespoon black cocoa powder (30g)")
    assert len(ings) == 2
    assert ings[0].quantity == 0.25
    assert ings[0].unit == "cup"
    assert ings[1].quantity == 1.0
    assert ings[1].unit == "tablespoon"
    for ing in ings:
        assert "black cocoa powder" in ing.name


def test_compound_qty_tbsp_plus_tsp():
    """'2 tablespoons + 1 teaspoon vanilla extract' → two ingredients."""
    ings = parse_ingredients("2 tablespoons + 1 teaspoon vanilla extract")
    assert len(ings) == 2
    assert ings[0].quantity == 2.0
    assert ings[0].unit == "tablespoon"
    assert ings[1].quantity == 1.0
    assert ings[1].unit == "teaspoon"
    for ing in ings:
        assert ing.name == "vanilla extract"


def test_compound_qty_no_false_positive():
    """'1 cup peanut butter + jelly swirl' — no unit after +, so no split."""
    ings = parse_ingredients("1 cup peanut butter + jelly swirl")
    assert len(ings) == 1


def test_compound_qty_normal_ingredient_unchanged():
    """'2 cups flour' — no + sign, normal single ingredient."""
    ings = parse_ingredients("2 cups flour")
    assert len(ings) == 1
    assert ings[0].quantity == 2.0
    assert ings[0].unit == "cup"
    assert ings[0].name == "flour"
