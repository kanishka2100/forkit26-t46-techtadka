"""Unit tests for the Cost & Margin Dashboard and Ingredient Substitution Analysis."""

import pytest
from app.schemas.dashboard import (
    RecipeCostingItem,
    RecipeCostingRequest,
    SubstitutionAnalysisRequest,
)
from app.services.dashboard_service import (
    analyze_substitution,
    calculate_recipe_costing,
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


def test_recipe_costing_yield_and_unit_conversions():
    """Verify unit conversions, yield %, shrinkage buffer, and batch portion costing."""
    req = RecipeCostingRequest(
        recipe_name="Test Butter Chicken",
        portions=10,
        shrinkage_percent=5.0,  # 5% cooking loss buffer
        target_food_cost_percent=30.0,
        packaging_cost_per_portion=15.0,
        delivery_commission_percent=22.0,
        menu_selling_price=350.0,
        sales_volume_level="high",
        currency="₹",
        ingredients=[
            # 1000g chicken breast at ₹300/kg, 80% yield (20% trim loss)
            RecipeCostingItem(
                name="Chicken Breast",
                ep_quantity=1000.0,
                unit="g",
                purchase_price=300.0,
                purchase_unit="kg",
                yield_percent=80.0,
            ),
            # 2 tbsp butter (~30g) at ₹500/kg, 100% yield
            RecipeCostingItem(
                name="Butter",
                ep_quantity=2.0,
                unit="tbsp",
                purchase_price=500.0,
                purchase_unit="kg",
                yield_percent=100.0,
            ),
        ],
    )
    res = calculate_recipe_costing(req)

    assert res.status == "success"
    assert res.portions == 10
    assert len(res.ingredients) == 2

    # Chicken AP calculation:
    # EP = 1000g, Yield = 80%, Shrinkage = 5%
    # AP = (1000 / 0.8) * 1.05 = 1312.5g = 1.3125 kg
    # Cost = 1.3125 * 300 = ₹393.75
    chicken = res.ingredients[0]
    assert chicken.ap_quantity == pytest.approx(1.312, abs=1e-2)
    assert chicken.cost == pytest.approx(393.75, abs=1e-1)

    assert res.total_batch_cost > 0
    assert res.cost_per_portion == pytest.approx(res.total_batch_cost / 10.0, rel=1e-2)
    # Target 30% food cost -> Recommended Dine-in Price = Cost / 0.30
    assert res.recommended_dine_in_price == pytest.approx(res.cost_per_portion / 0.30, rel=1e-2)


def test_delivery_pricing_and_menu_matrix():
    """Verify delivery platform price calculation and Kasavana & Smith matrix classifications."""
    # Case 1: Star (High margin + High volume)
    req_star = RecipeCostingRequest(
        recipe_name="Signature Biryani",
        portions=5,
        target_food_cost_percent=30.0,
        packaging_cost_per_portion=20.0,
        delivery_commission_percent=20.0,
        menu_selling_price=400.0,
        sales_volume_level="high",
        ingredients=[
            RecipeCostingItem(
                name="Rice & Spices",
                ep_quantity=500.0,
                unit="g",
                purchase_price=100.0,
                purchase_unit="kg",
                yield_percent=100.0,
            )
        ],
    )
    res_star = calculate_recipe_costing(req_star)
    assert res_star.menu_matrix_class == "Star"
    assert "🌟" in res_star.menu_matrix_badge
    # Delivery platform price should protect dine-in margin after 20% commission
    assert res_star.recommended_delivery_price > res_star.actual_selling_price

    # Case 2: Plowhorse (Low margin + High volume)
    req_plowhorse = RecipeCostingRequest(
        recipe_name="Budget Thali",
        portions=1,
        target_food_cost_percent=25.0,
        menu_selling_price=120.0,
        sales_volume_level="high",
        ingredients=[
            RecipeCostingItem(
                name="Rich Paneer",
                ep_quantity=200.0,
                unit="g",
                purchase_price=450.0,
                purchase_unit="kg",
                yield_percent=100.0,
            )
        ],
    )
    res_plow = calculate_recipe_costing(req_plowhorse)
    assert res_plow.menu_matrix_class == "Plowhorse"
    assert "🐎" in res_plow.menu_matrix_badge

    # Case 3: Puzzle (High margin + Low volume)
    req_puzzle = RecipeCostingRequest(
        recipe_name="Truffle Risotto",
        portions=1,
        target_food_cost_percent=30.0,
        menu_selling_price=600.0,
        sales_volume_level="low",
        ingredients=[
            RecipeCostingItem(
                name="Arborio Rice",
                ep_quantity=100.0,
                unit="g",
                purchase_price=200.0,
                purchase_unit="kg",
                yield_percent=100.0,
            )
        ],
    )
    res_puz = calculate_recipe_costing(req_puzzle)
    assert res_puz.menu_matrix_class == "Puzzle"
    assert "🧩" in res_puz.menu_matrix_badge
