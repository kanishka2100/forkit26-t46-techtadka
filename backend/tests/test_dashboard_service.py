"""Unit tests for the Cost & Margin Dashboard and Ingredient Substitution Analysis."""

import pytest
from app.schemas.dashboard import SubstitutionAnalysisRequest
from app.services.dashboard_service import (
    analyze_substitution,
    compute_replacement_quantity,
    resolve_ingredient,
)


def test_paneer_to_tofu_analysis():
    """Test analyzing Paneer to Tofu substitution in Paneer Butter Masala."""
    req = SubstitutionAnalysisRequest(
        dish_name="Paneer Butter Masala",
        missing_ingredient="Paneer",
        replacement_ingredient="Tofu",
        persons=5,
        selling_price_per_person=350.0,
        currency="₹",
    )
    res = analyze_substitution(req)

    assert res.status == "success"
    assert res.persons == 5
    assert res.currency == "₹"

    # Original Paneer checks
    assert "Paneer" in res.original.ingredient
    assert res.original.quantity_per_person == 150.0
    assert res.original.total_quantity == 750.0
    assert res.original.total_recipe_cost > 0
    assert res.original.total_calories > 0
    assert "Soft" in res.original.texture
    assert res.original.profit_margin is not None
    assert res.original.profit_margin > 0

    # Modified Tofu checks
    assert "Tofu" in res.modified.ingredient
    assert res.modified.quantity_per_person == 150.0
    assert res.modified.total_quantity == 750.0
    assert res.modified.cost_per_person < res.original.cost_per_person  # Tofu is more cost-effective
    assert res.modified.total_calories < res.original.total_calories  # Tofu has fewer calories
    assert "porous" in res.modified.texture.lower()
    assert res.modified.profit_margin > res.original.profit_margin  # Higher profit margin

    # Comparison rows
    params = [row.parameter for row in res.comparison]
    assert "Cost" in params
    assert "Calories" in params
    assert "Texture" in params
    assert "Ingredient Quantity" in params
    assert "Cost Per Person" in params
    assert "Profit Margin" in params

    cost_row = next(r for r in res.comparison if r.parameter == "Cost")
    assert cost_row.indicator == "green"  # Cost savings


def test_dynamic_headcount_scaling():
    """Test dynamic scaling across 5, 20, 100, and 200 people."""
    for count in [5, 20, 100, 200]:
        req = SubstitutionAnalysisRequest(
            dish_name="Vegetable Biryani",
            missing_ingredient="Paneer",
            replacement_ingredient="Tofu",
            persons=count,
            selling_price_per_person=300.0,
        )
        res = analyze_substitution(req)
        assert res.persons == count
        assert res.original.total_quantity == pytest.approx(150.0 * count)
        assert res.modified.total_quantity == pytest.approx(150.0 * count)
        assert res.original.total_recipe_cost == pytest.approx(res.original.cost_per_person * count, rel=1e-2)
        assert res.original.total_calories == res.original.calories_per_person * count


def test_replacement_quantity_calibration():
    """Verify calibrated culinary substitution ratios (not blindly 1:1 for moisture/fat shifts)."""
    # Butter -> Ghee (Ghee has 0 water, needs less quantity)
    ghee_qty = compute_replacement_quantity("Butter", 100.0, "Ghee")
    assert ghee_qty == 80.0

    # Butter -> Olive Oil (3:4 ratio)
    oil_qty = compute_replacement_quantity("Butter", 100.0, "Olive Oil")
    assert oil_qty == 75.0

    # Rice -> Cauliflower Rice (Needs more bulk for volumetric equivalent)
    cauli_qty = compute_replacement_quantity("Rice", 100.0, "Cauliflower Rice")
    assert cauli_qty == 125.0


def test_custom_ingredient_fallback_estimate():
    """Verify that uncatalogued custom ingredients are resolved with clear estimate labeling."""
    custom = resolve_ingredient("exotic dragonfruit seeds")
    assert custom["texture_is_estimate"] is True
    assert "Dragonfruit Seeds" in custom["canonical_name"]
