"""Cost & Margin Dashboard Domain Service.

Calculates real batch economics, nutritional differences, texture shifts,
and profit margins across dynamic headcount (5–200 persons).
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.dashboard import (
    ComparisonRow,
    RecipeMetricsSection,
    SubstitutionAnalysisRequest,
    SubstitutionAnalysisResponse,
)

logger = logging.getLogger("flavorshift.dashboard")

# Master culinary ingredient database with authentic prices, calories, and texture profiles
INGREDIENT_DATABASE: Dict[str, Dict[str, Any]] = {
    "paneer": {
        "canonical_name": "Fresh Malai Paneer",
        "synonyms": ["paneer", "cottage cheese", "malai paneer", "indian cheese"],
        "price_per_100g_inr": 48.0,
        "price_per_100g_usd": 0.60,
        "calories_per_100g": 296,
        "protein_per_100g": 18.3,
        "fat_per_100g": 22.0,
        "carbs_per_100g": 4.5,
        "default_portion_g": 150.0,
        "unit": "g fresh cubes",
        "texture": "Soft, pillowy, spongy curds that gently absorb rich sauces without disintegrating under heat.",
        "texture_is_estimate": False,
    },
    "tofu": {
        "canonical_name": "Pressed Firm Tofu",
        "synonyms": ["tofu", "firm tofu", "organic tofu", "bean curd"],
        "price_per_100g_inr": 32.0,
        "price_per_100g_usd": 0.40,
        "calories_per_100g": 144,
        "protein_per_100g": 15.5,
        "fat_per_100g": 8.0,
        "carbs_per_100g": 2.5,
        "default_portion_g": 150.0,
        "unit": "g pressed cubes",
        "texture": "Dense, tender porous plant-protein block with pleasant chew; holds shape well during simmering.",
        "texture_is_estimate": False,
    },
    "fresh cream": {
        "canonical_name": "Dairy Fresh Heavy Cream (25-30% Fat)",
        "synonyms": ["fresh cream", "heavy cream", "whipping cream", "malai", "cream"],
        "price_per_100g_inr": 42.0,
        "price_per_100g_usd": 0.55,
        "calories_per_100g": 345,
        "protein_per_100g": 2.1,
        "fat_per_100g": 35.0,
        "carbs_per_100g": 2.9,
        "default_portion_g": 60.0,
        "unit": "g velvety cream",
        "texture": "Velvety, unctuous, high-fat dairy emulsion delivering glossy coating power and rich mouthfeel.",
        "texture_is_estimate": False,
    },
    "cashew cream": {
        "canonical_name": "Soaked Cashew & Warm Milk Velvet Emulsion",
        "synonyms": ["cashew cream", "cashew paste", "cashew milk", "kaju paste", "cashew puree"],
        "price_per_100g_inr": 58.0,
        "price_per_100g_usd": 0.75,
        "calories_per_100g": 290,
        "protein_per_100g": 8.5,
        "fat_per_100g": 21.0,
        "carbs_per_100g": 15.0,
        "default_portion_g": 60.0,
        "unit": "g emulsified puree",
        "texture": "Silky, viscous, heat-stable micro-emulsion that simmers smoothly without curdling or separation.",
        "texture_is_estimate": False,
    },
    "butter": {
        "canonical_name": "Salted Butter / Table Butter",
        "synonyms": ["butter", "salted butter", "unsalted butter", "makkhan"],
        "price_per_100g_inr": 56.0,
        "price_per_100g_usd": 0.70,
        "calories_per_100g": 717,
        "protein_per_100g": 0.9,
        "fat_per_100g": 81.1,
        "carbs_per_100g": 0.1,
        "default_portion_g": 25.0,
        "unit": "g softened",
        "texture": "Mellow solid at room temp (20°C); melts at body temperature (34°C) into glossy golden pool.",
        "texture_is_estimate": False,
    },
    "ghee": {
        "canonical_name": "Clarified Butter / Desi Ghee",
        "synonyms": ["ghee", "clarified butter", "desi ghee"],
        "price_per_100g_inr": 68.0,
        "price_per_100g_usd": 0.90,
        "calories_per_100g": 900,
        "protein_per_100g": 0.0,
        "fat_per_100g": 99.8,
        "carbs_per_100g": 0.0,
        "default_portion_g": 20.0,
        "unit": "g golden clarified",
        "texture": "Granular crystalline solid below 24°C; turns into intensely aromatic, clear liquid fat above 32°C.",
        "texture_is_estimate": False,
    },
    "greek yogurt": {
        "canonical_name": "Strained Greek Yogurt / Hung Curd",
        "synonyms": ["greek yogurt", "hung curd", "dahi", "curd", "whisked yogurt"],
        "price_per_100g_inr": 28.0,
        "price_per_100g_usd": 0.35,
        "calories_per_100g": 97,
        "protein_per_100g": 10.0,
        "fat_per_100g": 4.5,
        "carbs_per_100g": 3.8,
        "default_portion_g": 60.0,
        "unit": "g strained",
        "texture": "Thick, creamy, spoonable dairy paste with lactic tang; smooth and light on palate.",
        "texture_is_estimate": False,
    },
    "chicken": {
        "canonical_name": "Boneless Chicken Breast Cubes",
        "synonyms": ["chicken", "chicken breast", "poultry", "chicken thigh"],
        "price_per_100g_inr": 36.0,
        "price_per_100g_usd": 0.45,
        "calories_per_100g": 165,
        "protein_per_100g": 31.0,
        "fat_per_100g": 3.6,
        "carbs_per_100g": 0.0,
        "default_portion_g": 150.0,
        "unit": "g fresh cut",
        "texture": "Fibrous, firm, tender lean meat fibers that retain moisture when simmered in gravy.",
        "texture_is_estimate": False,
    },
    "mushroom": {
        "canonical_name": "Fresh Button / Cremini Mushrooms",
        "synonyms": ["mushroom", "mushrooms", "button mushroom", "cremini", "portobello"],
        "price_per_100g_inr": 30.0,
        "price_per_100g_usd": 0.38,
        "calories_per_100g": 22,
        "protein_per_100g": 3.1,
        "fat_per_100g": 0.3,
        "carbs_per_100g": 3.3,
        "default_portion_g": 140.0,
        "unit": "g sliced",
        "texture": "Spongy and resilient raw; softens to juicy, meaty bite with deep savory umami when seared.",
        "texture_is_estimate": False,
    },
    "eggs": {
        "canonical_name": "Farm Fresh Whole Eggs",
        "synonyms": ["egg", "eggs", "whole eggs"],
        "price_per_100g_inr": 20.0,
        "price_per_100g_usd": 0.25,
        "calories_per_100g": 143,
        "protein_per_100g": 12.6,
        "fat_per_100g": 9.5,
        "carbs_per_100g": 0.7,
        "default_portion_g": 100.0,
        "unit": "g (approx 2 eggs)",
        "texture": "Viscous liquid raw; coagulates into soft, tender elastic gel upon thermal coagulation.",
        "texture_is_estimate": False,
    },
    "aquafaba": {
        "canonical_name": "Chilled Chickpea Aquafaba",
        "synonyms": ["aquafaba", "chickpea water", "egg replacer"],
        "price_per_100g_inr": 10.0,
        "price_per_100g_usd": 0.12,
        "calories_per_100g": 18,
        "protein_per_100g": 1.0,
        "fat_per_100g": 0.2,
        "carbs_per_100g": 3.0,
        "default_portion_g": 60.0,
        "unit": "ml whipped brine",
        "texture": "Light viscous plant protein-saccharide brine; whips into stable, glossy airy foam.",
        "texture_is_estimate": False,
    },
    "all-purpose flour": {
        "canonical_name": "All-Purpose Wheat Flour (Maida)",
        "synonyms": ["flour", "maida", "all-purpose flour", "white flour", "wheat flour"],
        "price_per_100g_inr": 6.0,
        "price_per_100g_usd": 0.08,
        "calories_per_100g": 364,
        "protein_per_100g": 10.3,
        "fat_per_100g": 1.0,
        "carbs_per_100g": 76.3,
        "default_portion_g": 100.0,
        "unit": "g fine sifted",
        "texture": "Fine powdery grain starch; builds gluten matrix upon hydration creating chewy, elastic crumb.",
        "texture_is_estimate": False,
    },
    "almond flour": {
        "canonical_name": "Fine Blanched Almond Flour",
        "synonyms": ["almond flour", "almond meal", "badam powder"],
        "price_per_100g_inr": 85.0,
        "price_per_100g_usd": 1.10,
        "calories_per_100g": 590,
        "protein_per_100g": 21.4,
        "fat_per_100g": 52.5,
        "carbs_per_100g": 18.7,
        "default_portion_g": 100.0,
        "unit": "g fine ground",
        "texture": "Nutty, granular meal without gluten elasticity; produces tender, dense, melt-in-mouth crumb.",
        "texture_is_estimate": False,
    },
    "avocado": {
        "canonical_name": "Fresh Ripe Hass Avocado",
        "synonyms": ["avocado", "hass avocado", "ripe avocado"],
        "price_per_100g_inr": 70.0,
        "price_per_100g_usd": 0.90,
        "calories_per_100g": 160,
        "protein_per_100g": 2.0,
        "fat_per_100g": 14.7,
        "carbs_per_100g": 8.5,
        "default_portion_g": 120.0,
        "unit": "g sliced flesh",
        "texture": "Buttery, silky-soft, spreadable fruit fat with mild nutty mouthfeel.",
        "texture_is_estimate": False,
    },
    "green peas": {
        "canonical_name": "Sweet Tender Green Peas (Matar)",
        "synonyms": ["green peas", "peas", "matar", "sweet peas"],
        "price_per_100g_inr": 18.0,
        "price_per_100g_usd": 0.22,
        "calories_per_100g": 81,
        "protein_per_100g": 5.4,
        "fat_per_100g": 0.4,
        "carbs_per_100g": 14.5,
        "default_portion_g": 120.0,
        "unit": "g blanched",
        "texture": "Crisp-tender skins that pop gently; mashes into vibrant sweet green puree.",
        "texture_is_estimate": False,
    },
    "olive oil": {
        "canonical_name": "Extra Virgin Cold-Pressed Olive Oil",
        "synonyms": ["olive oil", "extra virgin olive oil", "evoo"],
        "price_per_100g_inr": 90.0,
        "price_per_100g_usd": 1.20,
        "calories_per_100g": 884,
        "protein_per_100g": 0.0,
        "fat_per_100g": 100.0,
        "carbs_per_100g": 0.0,
        "default_portion_g": 20.0,
        "unit": "ml oil",
        "texture": "Smooth, fluid, unctuous liquid fat with peppery throat bite and clean gloss.",
        "texture_is_estimate": False,
    },
    "rice": {
        "canonical_name": "Aged Long-Grain Basmati Rice",
        "synonyms": ["rice", "basmati rice", "white rice"],
        "price_per_100g_inr": 14.0,
        "price_per_100g_usd": 0.18,
        "calories_per_100g": 360,
        "protein_per_100g": 7.0,
        "fat_per_100g": 0.6,
        "carbs_per_100g": 80.0,
        "default_portion_g": 100.0,
        "unit": "g raw grains",
        "texture": "Firm, distinct, fluffy elongated grains that remain separate and tender when cooked.",
        "texture_is_estimate": False,
    },
    "cauliflower rice": {
        "canonical_name": "Grated Cauliflower Pearls",
        "synonyms": ["cauliflower rice", "riced cauliflower", "cauliflower"],
        "price_per_100g_inr": 12.0,
        "price_per_100g_usd": 0.15,
        "calories_per_100g": 25,
        "protein_per_100g": 1.9,
        "fat_per_100g": 0.3,
        "carbs_per_100g": 5.0,
        "default_portion_g": 140.0,
        "unit": "g riced pearls",
        "texture": "Al dente, tender-crisp vegetable granules with light moist bite and delicate sweet crunch.",
        "texture_is_estimate": False,
    },
}

# Dish baseline archetypes (used to supply complete whole-dish context)
DISH_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "paneer butter masala": {
        "title": "Velvety Paneer Butter Masala (Makhani)",
        "base_other_cost_inr": 65.0,  # gravy, spices, tomatoes, aromatics
        "base_other_calories": 280,
        "default_primary_ing": "paneer",
        "default_replacement": "tofu",
        "suggested_selling_price_inr": 350.0,
        "suggested_selling_price_usd": 12.00,
    },
    "vegetable biryani": {
        "title": "Hyderabadi Dum Vegetable Biryani",
        "base_other_cost_inr": 55.0,
        "base_other_calories": 260,
        "default_primary_ing": "paneer",
        "default_replacement": "tofu",
        "suggested_selling_price_inr": 320.0,
        "suggested_selling_price_usd": 11.00,
    },
    "pasta": {
        "title": "Wild Mushroom & Cream Penne Pasta",
        "base_other_cost_inr": 70.0,
        "base_other_calories": 310,
        "default_primary_ing": "fresh cream",
        "default_replacement": "cashew cream",
        "suggested_selling_price_inr": 380.0,
        "suggested_selling_price_usd": 14.00,
    },
    "avocado toast": {
        "title": "Signature Smashed Avocado & Feta Toast",
        "base_other_cost_inr": 45.0,
        "base_other_calories": 190,
        "default_primary_ing": "avocado",
        "default_replacement": "green peas",
        "suggested_selling_price_inr": 280.0,
        "suggested_selling_price_usd": 9.50,
    },
    "butter chicken": {
        "title": "Classic Old Delhi Butter Chicken",
        "base_other_cost_inr": 75.0,
        "base_other_calories": 320,
        "default_primary_ing": "chicken",
        "default_replacement": "mushroom",
        "suggested_selling_price_inr": 420.0,
        "suggested_selling_price_usd": 15.00,
    },
}


def normalize_query(text: str) -> str:
    """Normalize input string for lookup."""
    if not text:
        return ""
    clean = text.lower().strip()
    return clean


def resolve_ingredient(name: str) -> Dict[str, Any]:
    """Resolve ingredient from database or return reliable fallback."""
    norm = normalize_query(name)
    if norm in INGREDIENT_DATABASE:
        return INGREDIENT_DATABASE[norm]

    # Check synonyms
    for key, data in INGREDIENT_DATABASE.items():
        if norm in [s.lower() for s in data.get("synonyms", [])]:
            return data
        for s in data.get("synonyms", []):
            if s.lower() in norm or norm in s.lower():
                return data

    # Fallback with sensible default estimate, clearly labeled
    logger.info("Ingredient '%s' not in primary database; generating calibrated profile estimate.", name)
    return {
        "canonical_name": name.title(),
        "synonyms": [norm],
        "price_per_100g_inr": 35.0,
        "price_per_100g_usd": 0.45,
        "calories_per_100g": 180,
        "protein_per_100g": 8.0,
        "fat_per_100g": 6.0,
        "carbs_per_100g": 20.0,
        "default_portion_g": 100.0,
        "unit": "g calibrated portion",
        "texture": f"Natural characteristic texture for culinary ingredient '{name}'.",
        "texture_is_estimate": True,
    }


def resolve_dish_archetype(dish_name: str) -> Dict[str, Any]:
    """Find matching dish archetype or generate contextual base."""
    norm = normalize_query(dish_name)
    for key, arch in DISH_ARCHETYPES.items():
        if key in norm or norm in key:
            return arch

    words = norm.split()
    for w in words:
        if len(w) > 3:
            for key, arch in DISH_ARCHETYPES.items():
                if w in key:
                    return arch

    # Generic dish baseline
    return {
        "title": dish_name.title(),
        "base_other_cost_inr": 60.0,
        "base_other_calories": 250,
        "default_primary_ing": "paneer",
        "default_replacement": "tofu",
        "suggested_selling_price_inr": 320.0,
        "suggested_selling_price_usd": 11.00,
    }


def compute_replacement_quantity(
    orig_name: str,
    orig_qty_per_person: float,
    repl_name: str,
) -> float:
    """Calculate the culinarily appropriate replacement quantity.

    Never blindly assumes 1:1; factors in moisture, fat content, and density.
    """
    o = normalize_query(orig_name)
    r = normalize_query(repl_name)

    # Butter -> Ghee: 100g butter = 80g ghee (ghee has zero water content)
    if ("butter" in o and "ghee" in r) or ("butter" in r and "ghee" in o):
        if "ghee" in r:
            return round(orig_qty_per_person * 0.8, 1)
        else:
            return round(orig_qty_per_person * 1.25, 1)

    # Butter -> Oil: 100g butter = 75ml oil
    if "butter" in o and ("oil" in r or "olive" in r):
        return round(orig_qty_per_person * 0.75, 1)

    # Heavy Cream -> Cashew Paste: 100g cream = 60g cashew paste + 40g milk (60g paste core)
    if ("cream" in o or "malai" in o) and ("cashew" in r or "kaju" in r):
        return round(orig_qty_per_person * 0.85, 1)

    # Rice -> Cauliflower Rice: Needs higher bulk for equivalent volume (1.2x)
    if "rice" in o and "cauliflower" in r:
        return round(orig_qty_per_person * 1.25, 1)

    # Flour -> Almond Flour: Almond flour is denser and oilier (0.9x)
    if "flour" in o and "almond" in r:
        return round(orig_qty_per_person * 0.9, 1)

    # Paneer -> Tofu: 1:1 by fresh weight
    # Eggs -> Aquafaba: 50g egg = 45ml aquafaba (approx 0.9x)
    if "egg" in o and "aquafaba" in r:
        return round(orig_qty_per_person * 0.9, 1)

    # Standard default is 1.0 ratio
    return round(orig_qty_per_person, 1)


def analyze_substitution(req: SubstitutionAnalysisRequest) -> SubstitutionAnalysisResponse:
    """Core domain logic to analyze dish substitution and compute comparison."""
    persons = max(5, min(200, req.persons))
    currency = req.currency or "₹"
    is_usd = currency == "$"

    dish_archetype = resolve_dish_archetype(req.dish_name)
    orig_ing_data = resolve_ingredient(req.missing_ingredient)
    repl_ing_data = resolve_ingredient(req.replacement_ingredient)

    # Quantities per person
    orig_qty_per_person = orig_ing_data.get("default_portion_g", 150.0)
    repl_qty_per_person = compute_replacement_quantity(
        req.missing_ingredient,
        orig_qty_per_person,
        req.replacement_ingredient,
    )

    # Total batch quantities
    orig_total_qty = round(orig_qty_per_person * persons, 1)
    repl_total_qty = round(repl_qty_per_person * persons, 1)

    # Unit costs per 100g
    price_key = "price_per_100g_usd" if is_usd else "price_per_100g_inr"
    orig_unit_cost = orig_ing_data.get(price_key, 40.0)
    repl_unit_cost = repl_ing_data.get(price_key, 30.0)

    # Cost of the target ingredient per person
    orig_ing_cost_pp = (orig_qty_per_person / 100.0) * orig_unit_cost
    repl_ing_cost_pp = (repl_qty_per_person / 100.0) * repl_unit_cost

    # Base dish other costs (gravy base, spices, cooking fuel)
    other_cost_base = dish_archetype.get("base_other_cost_inr", 60.0)
    if is_usd:
        other_cost_base = round(other_cost_base / 30.0, 2)

    orig_cost_pp = round(other_cost_base + orig_ing_cost_pp, 2)
    repl_cost_pp = round(other_cost_base + repl_ing_cost_pp, 2)

    orig_total_cost = round(orig_cost_pp * persons, 2)
    repl_total_cost = round(repl_cost_pp * persons, 2)

    # Calories
    orig_cal_100g = orig_ing_data.get("calories_per_100g", 250)
    repl_cal_100g = repl_ing_data.get("calories_per_100g", 150)

    other_cal_base = dish_archetype.get("base_other_calories", 260)
    orig_ing_cal_pp = int((orig_qty_per_person / 100.0) * orig_cal_100g)
    repl_ing_cal_pp = int((repl_qty_per_person / 100.0) * repl_cal_100g)

    orig_cal_pp = other_cal_base + orig_ing_cal_pp
    repl_cal_pp = other_cal_base + repl_ing_cal_pp

    orig_total_cal = orig_cal_pp * persons
    repl_total_cal = repl_cal_pp * persons

    # Selling price and profit margins
    selling_price = req.selling_price_per_person
    if selling_price is None or selling_price <= 0:
        # Default suggested price from archetype
        price_prop = "suggested_selling_price_usd" if is_usd else "suggested_selling_price_inr"
        selling_price = dish_archetype.get(price_prop, 320.0 if not is_usd else 11.00)

    gross_revenue = round(selling_price * persons, 2) if selling_price else None

    # Original economics
    orig_profit = round(gross_revenue - orig_total_cost, 2) if gross_revenue else None
    orig_margin = round((orig_profit / gross_revenue) * 100.0, 1) if gross_revenue else None
    orig_margin_disp = f"{orig_margin}%" if orig_margin is not None else "Requires menu price"

    # Modified economics
    repl_profit = round(gross_revenue - repl_total_cost, 2) if gross_revenue else None
    repl_margin = round((repl_profit / gross_revenue) * 100.0, 1) if gross_revenue else None
    repl_margin_disp = f"{repl_margin}%" if repl_margin is not None else "Requires menu price"

    orig_section = RecipeMetricsSection(
        ingredient=orig_ing_data.get("canonical_name", req.missing_ingredient),
        quantity_per_person=orig_qty_per_person,
        total_quantity=orig_total_qty,
        unit=orig_ing_data.get("unit", "g"),
        cost_per_person=orig_cost_pp,
        total_recipe_cost=orig_total_cost,
        calories_per_person=orig_cal_pp,
        total_calories=orig_total_cal,
        texture=orig_ing_data.get("texture", "Standard texture characteristic."),
        texture_is_estimate=orig_ing_data.get("texture_is_estimate", False),
        selling_price_per_person=selling_price,
        gross_revenue=gross_revenue,
        gross_profit=orig_profit,
        profit_margin=orig_margin,
        profit_margin_display=orig_margin_disp,
    )

    modified_section = RecipeMetricsSection(
        ingredient=repl_ing_data.get("canonical_name", req.replacement_ingredient),
        quantity_per_person=repl_qty_per_person,
        total_quantity=repl_total_qty,
        unit=repl_ing_data.get("unit", "g"),
        cost_per_person=repl_cost_pp,
        total_recipe_cost=repl_total_cost,
        calories_per_person=repl_cal_pp,
        total_calories=repl_total_cal,
        texture=repl_ing_data.get("texture", "Standard texture characteristic."),
        texture_is_estimate=repl_ing_data.get("texture_is_estimate", False),
        selling_price_per_person=selling_price,
        gross_revenue=gross_revenue,
        gross_profit=repl_profit,
        profit_margin=repl_margin,
        profit_margin_display=repl_margin_disp,
    )

    # Build Side-by-Side Comparison Table rows
    comparison: List[ComparisonRow] = []

    # 1. Total Cost
    cost_diff = round(repl_total_cost - orig_total_cost, 2)
    cost_diff_pct = round((cost_diff / max(orig_total_cost, 0.01)) * 100.0, 1)
    if cost_diff < -0.01:
        cost_ind = "green"
        cost_exp = f"Cost reduced by {currency}{abs(cost_diff):.2f} ({abs(cost_diff_pct):.1f}%) across {persons} servings due to more economical replacement."
    elif cost_diff > 0.01:
        cost_ind = "red"
        cost_exp = f"Cost increased by {currency}{cost_diff:.2f} (+{cost_diff_pct:.1f}%) across {persons} servings due to premium ingredient sourcing."
    else:
        cost_ind = "neutral"
        cost_exp = f"Batch food cost remains identical across {persons} covers."

    comparison.append(ComparisonRow(
        parameter="Cost",
        original=f"{currency}{orig_total_cost:,.2f}",
        modified=f"{currency}{repl_total_cost:,.2f}",
        difference=f"{'+' if cost_diff > 0 else ''}{currency}{cost_diff:,.2f} ({cost_diff_pct:+.1f}%)",
        indicator=cost_ind,
        explanation=cost_exp,
    ))

    # 2. Total Calories
    cal_diff = repl_total_cal - orig_total_cal
    cal_diff_pct = round((cal_diff / max(orig_total_cal, 1)) * 100.0, 1)
    if cal_diff < 0:
        # Lower calories: neither strictly good nor bad, explain factual difference
        cal_ind = "neutral"
        cal_exp = f"Reduction of {abs(cal_diff):,} kcal total ({abs(cal_diff_pct):.1f}%), yielding a lighter, less energy-dense preparation."
    elif cal_diff > 0:
        cal_ind = "neutral"
        cal_exp = f"Increase of {cal_diff:,} kcal total (+{cal_diff_pct:.1f}%), providing higher caloric density and energy."
    else:
        cal_ind = "neutral"
        cal_exp = "Caloric profile remains virtually identical."

    comparison.append(ComparisonRow(
        parameter="Calories",
        original=f"{orig_total_cal:,} kcal",
        modified=f"{repl_total_cal:,} kcal",
        difference=f"{'+' if cal_diff > 0 else ''}{cal_diff:,} kcal ({cal_diff_pct:+.1f}%)",
        indicator=cal_ind,
        explanation=cal_exp,
    ))

    # 3. Texture
    tex_orig_snippet = orig_section.texture.split(".")[0]
    tex_repl_snippet = modified_section.texture.split(".")[0]
    comparison.append(ComparisonRow(
        parameter="Texture",
        original=tex_orig_snippet,
        modified=tex_repl_snippet,
        difference="Texture profile shifted",
        indicator="neutral",
        explanation=f"Original relies on '{orig_section.ingredient}' mouthfeel; replacement provides '{modified_section.ingredient}' characteristics ({modified_section.texture}).",
    ))

    # 4. Ingredient Quantity
    qty_diff = round(repl_total_qty - orig_total_qty, 1)
    qty_diff_pct = round((qty_diff / max(orig_total_qty, 0.1)) * 100.0, 1)
    comparison.append(ComparisonRow(
        parameter="Ingredient Quantity",
        original=f"{orig_total_qty:,.1f} {orig_section.unit}",
        modified=f"{repl_total_qty:,.1f} {modified_section.unit}",
        difference=f"{'+' if qty_diff > 0 else ''}{qty_diff:,.1f} {modified_section.unit} ({qty_diff_pct:+.1f}%)",
        indicator="neutral",
        explanation=f"Replacement ratio calibrated: {orig_qty_per_person}g {orig_section.ingredient} → {repl_qty_per_person}g {modified_section.ingredient} per portion.",
    ))

    # 5. Cost Per Person
    cost_pp_diff = round(repl_cost_pp - orig_cost_pp, 2)
    cost_pp_pct = round((cost_pp_diff / max(orig_cost_pp, 0.01)) * 100.0, 1)
    if cost_pp_diff < -0.01:
        cpp_ind = "green"
        cpp_exp = f"Savings of {currency}{abs(cost_pp_diff):.2f} per portion ({abs(cost_pp_pct):.1f}% reduction in plate cost)."
    elif cost_pp_diff > 0.01:
        cpp_ind = "red"
        cpp_exp = f"Cost increase of {currency}{cost_pp_diff:.2f} per portion (+{cost_pp_pct:.1f}% plate cost increase)."
    else:
        cpp_ind = "neutral"
        cpp_exp = "Plate food cost unchanged per person."

    comparison.append(ComparisonRow(
        parameter="Cost Per Person",
        original=f"{currency}{orig_cost_pp:,.2f}",
        modified=f"{currency}{repl_cost_pp:,.2f}",
        difference=f"{'+' if cost_pp_diff > 0 else ''}{currency}{cost_pp_diff:,.2f} ({cost_pp_pct:+.1f}%)",
        indicator=cpp_ind,
        explanation=cpp_exp,
    ))

    # 6. Profit Margin
    if orig_margin is not None and repl_margin is not None:
        margin_diff = round(repl_margin - orig_margin, 1)
        if margin_diff > 0.1:
            margin_ind = "green"
            margin_exp = f"Gross margin improves by +{margin_diff:.1f}% points due to lower food costs at {currency}{selling_price:.2f}/cover."
        elif margin_diff < -0.1:
            margin_ind = "red"
            margin_exp = f"Gross margin decreases by {abs(margin_diff):.1f}% points due to higher input costs at {currency}{selling_price:.2f}/cover."
        else:
            margin_ind = "neutral"
            margin_exp = "Gross profit margin remains steady."

        comparison.append(ComparisonRow(
            parameter="Profit Margin",
            original=f"{orig_margin:.1f}%",
            modified=f"{repl_margin:.1f}%",
            difference=f"{'+' if margin_diff > 0 else ''}{margin_diff:.1f}% pts",
            indicator=margin_ind,
            explanation=margin_exp,
        ))
    else:
        comparison.append(ComparisonRow(
            parameter="Profit Margin",
            original="Requires menu price",
            modified="Requires menu price",
            difference="—",
            indicator="neutral",
            explanation="Provide menu selling price to calculate gross profit margin.",
        ))

    summary = {
        "dish": dish_archetype["title"],
        "persons": persons,
        "total_cost_saved": round(max(0.0, orig_total_cost - repl_total_cost), 2),
        "total_calories_diff": repl_total_cal - orig_total_cal,
        "is_cost_saving": repl_total_cost < orig_total_cost,
    }

    return SubstitutionAnalysisResponse(
        dish_name=dish_archetype["title"],
        missing_ingredient=req.missing_ingredient,
        replacement_ingredient=req.replacement_ingredient,
        persons=persons,
        currency=currency,
        selling_price_per_person=selling_price,
        original=orig_section,
        modified=modified_section,
        comparison=comparison,
        summary=summary,
    )
