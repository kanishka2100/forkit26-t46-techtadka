"""Pydantic v2 schemas for the Cost & Margin Dashboard and Ingredient Substitution Analysis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SubstitutionAnalysisRequest(BaseModel):
    """Payload to analyze recipe ingredient substitution and batch economics."""

    dish_name: str = Field(..., min_length=1, max_length=120, examples=["Paneer Butter Masala"])
    missing_ingredient: str = Field(..., min_length=1, max_length=80, examples=["Paneer"])
    replacement_ingredient: str = Field(..., min_length=1, max_length=80, examples=["Tofu"])
    persons: int = Field(5, ge=5, le=200, description="Headcount for batch scaling (5 to 200 covers)")
    selling_price_per_person: Optional[float] = Field(None, ge=0, description="Menu selling price per person")
    currency: Optional[str] = Field("₹", description="Currency symbol: ₹ or $")


class RecipeMetricsSection(BaseModel):
    """Nutritional, financial, and textural metrics for a recipe variant."""

    ingredient: str
    quantity_per_person: float
    total_quantity: float
    unit: str
    cost_per_person: float
    total_recipe_cost: float
    calories_per_person: int
    total_calories: int
    texture: str
    texture_is_estimate: bool = False
    selling_price_per_person: Optional[float] = None
    gross_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    profit_margin: Optional[float] = None
    profit_margin_display: Optional[str] = None


class ComparisonRow(BaseModel):
    """A parameter comparison between original and modified recipes."""

    parameter: str
    original: str
    modified: str
    difference: str
    indicator: str  # "green", "red", "neutral"
    explanation: str


class SubstitutionAnalysisResponse(BaseModel):
    """Complete substitution analysis and side-by-side comparison output."""

    status: str = "success"
    dish_name: str
    missing_ingredient: str
    replacement_ingredient: str
    persons: int
    currency: str
    selling_price_per_person: Optional[float] = None
    original: RecipeMetricsSection
    modified: RecipeMetricsSection
    comparison: List[ComparisonRow]
    summary: Dict[str, Any]


class RecipeCostingItem(BaseModel):
    """Single ingredient line item in a culinary recipe costing sheet."""

    name: str = Field(..., examples=["Basmati Rice"])
    ep_quantity: float = Field(..., ge=0, examples=[500.0])
    unit: str = Field("g", description="Recipe measurement unit: g, kg, ml, l, pcs, tsp, tbsp")
    purchase_price: float = Field(..., ge=0, description="As Purchased price per purchase unit")
    purchase_unit: str = Field("kg", description="Packaging unit: kg, l, pcs, g")
    yield_percent: float = Field(100.0, ge=1.0, le=100.0, description="Edible portion yield percentage (e.g. 85 for onion trim loss)")


class RecipeCostingRequest(BaseModel):
    """OpenKitchen & Restaurant Menu Engineering recipe costing and pricing request."""

    recipe_name: str = Field("Custom Recipe", min_length=1, max_length=120)
    portions: int = Field(10, ge=1, le=1000, description="Number of portions / covers in batch")
    shrinkage_percent: float = Field(3.0, ge=0.0, le=50.0, description="Cooking evaporation / waste shrinkage buffer %")
    target_food_cost_percent: float = Field(30.0, ge=5.0, le=90.0, description="Target food cost % (e.g. 28% to 35%)")
    packaging_cost_per_portion: float = Field(15.0, ge=0.0, description="Takeout / delivery container packaging cost")
    delivery_commission_percent: float = Field(22.0, ge=0.0, le=50.0, description="Aggregator fee % (e.g. 22% Swiggy/Zomato)")
    menu_selling_price: Optional[float] = Field(None, ge=0.0, description="Actual menu retail price")
    sales_volume_level: str = Field("high", description="Sales popularity level: 'high' or 'low' for Kasavana & Smith matrix")
    currency: Optional[str] = Field("₹", description="Currency symbol: ₹ or $")
    ingredients: List[RecipeCostingItem] = Field(default_factory=list)


class CostingItemResult(BaseModel):
    """Calculated AP quantity and line-item cost for an ingredient."""

    name: str
    ep_quantity: float
    unit: str
    yield_percent: float
    ap_quantity: float
    ap_unit: str
    cost: float
    cost_share_percent: float


class RecipeCostingResponse(BaseModel):
    """Comprehensive culinary recipe costing, pricing, and menu matrix output."""

    status: str = "success"
    recipe_name: str
    portions: int
    currency: str
    total_batch_cost: float
    cost_per_portion: float
    recommended_dine_in_price: float
    actual_selling_price: float
    actual_food_cost_percent: float
    actual_gross_margin_percent: float
    contribution_margin: float
    packaging_cost: float
    delivery_commission_percent: float
    recommended_delivery_price: float
    net_delivery_payout: float
    menu_matrix_class: str  # Star, Plowhorse, Puzzle, Dog
    menu_matrix_badge: str
    menu_matrix_strategy: str
    ingredients: List[CostingItemResult]
