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
