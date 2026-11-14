"""Cost & Margin Dashboard Router.

Exposes endpoints for the 4-step ingredient substitution analysis workflow,
dynamic 5–200 headcount scaling, and batch margin simulations.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from app.schemas.dashboard import (
    SubstitutionAnalysisRequest,
    SubstitutionAnalysisResponse,
)
from app.services.dashboard_service import (
    INGREDIENT_DATABASE,
    analyze_substitution,
)

router = APIRouter(prefix="/dashboard", tags=["Cost & Margin Dashboard"])


@router.post("/analyze-substitution", response_model=SubstitutionAnalysisResponse)
async def api_analyze_substitution(request: SubstitutionAnalysisRequest):
    """Analyse recipe substitution with real ingredient metrics and batch scaling.

    Step 1: Dish Name (e.g. Paneer Butter Masala, Vegetable Biryani, Pasta)
    Step 2: Missing Ingredient (e.g. Paneer)
    Step 3: Replacement Ingredient (e.g. Tofu)
    Step 4: Number of People (5–200 covers)
    """
    try:
        return analyze_substitution(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze substitution: {str(e)}"
        )


@router.get("/ingredients")
async def get_dashboard_ingredients():
    """List available baseline ingredients with their nutritional & cost specs."""
    return {
        "status": "success",
        "count": len(INGREDIENT_DATABASE),
        "ingredients": [
            {
                "key": key,
                "canonical_name": data.get("canonical_name"),
                "price_per_100g_inr": data.get("price_per_100g_inr"),
                "price_per_100g_usd": data.get("price_per_100g_usd"),
                "calories_per_100g": data.get("calories_per_100g"),
                "texture": data.get("texture"),
            }
            for key, data in INGREDIENT_DATABASE.items()
        ]
    }
