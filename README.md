# FlavorShift AI 🍳✨
### Intelligent Culinary Ingredient Substitution & Human Taste Validation Platform

> AI-powered culinary intelligence that replaces missing or costly recipe ingredients with scientifically validated alternatives, exact mathematical substitution ratios, and crowdsourced Human Taste Validation (HTV).

| | |
|---|---|
| **Team** | `t46` · TechTadka |
| **Members** | Kanishka ([@kanishka2100](https://github.com/kanishka2100)) |
| **Track / Problem Statement** | FoodoScope Hackathon Track — Intelligent Culinary Substitution & Smart Cooking Assistant |
| **FoodoScope APIs Used** | ☑ RecipeDB · ☑ FlavorDB |
| **Live Working Demo** | [https://kanishka2100.github.io/forkit26-t46-techtadka/](https://kanishka2100.github.io/forkit26-t46-techtadka/) |
| **Hackathon Repository** | [https://github.com/Fork-IT-2026-Esya/forkit26-t46-techtadka](https://github.com/Fork-IT-2026-Esya/forkit26-t46-techtadka) |

---

## The Problem

Every day, home cooks, cloud kitchens, and culinary operators encounter severe kitchen friction:
1. **Missing Ingredient Friction**: A cook is halfway through preparing a dish and discovers an essential ingredient is absent. Blind substitutions frequently fail under heat (e.g. cold milk curdling in acidic tomato gravy).
2. **High Cost & Seasonal Inflation Barrier**: Premium staples like dairy heavy cream, imported mascarpone cheese, Hass avocados, pine nuts, and truffle oil suffer volatile price spikes.
3. **Lack of Verified Substitution Guidance**: Standard search engines return generic text lists without exact mathematical conversion ratios, moisture/fat compensation, or evidence that cooks have validated the taste.

---

## What We Built

**FlavorShift AI** is an intelligent culinary substitution platform designed as a clean, premium, mobile-responsive Single Page Application (SPA) paired with a high-performance FastAPI intelligence backend:

1. **AI Swap Lab (Flagship Engine)**: Instant substitution workspace for everyday and premium ingredients (Fresh Cream $\rightarrow$ Cashew-Milk Emulsion, Mascarpone $\rightarrow$ Hung Curd + Cream, Avocado $\rightarrow$ Sweet Pea Herb Puree, etc.) with dynamic live ratio conversions.
2. **Mathematical Flavor Identity Engine**: Ranks substitute ingredients using multi-criteria weighted scoring:
   $$\text{Score} = \text{Gate} \times (0.40 \times F + 0.40 \times R + 0.20 \times C)$$
   - $F$: Flavor chemical similarity cosine vector match.
   - $R$: Recipe compatibility and pairwise ingredient co-occurrence affinity.
   - $C$: Cost efficiency ($\min(1.0, \text{Price}_{\text{orig}} / \text{Price}_{\text{cand}})$).
   - $\text{Gate}$: Allergen, dietary (Vegan/Vegetarian/Gluten-Free), and role safety gate.
3. **Human Taste Validation (HTV) Hub**: Crowdsourced validation database featuring blind taste tests, texture/mouthfeel ratings, and photographic kitchen proof.
4. **Interactive RecipeDB Explorer**: Authentic culinary database with dynamic headcount scaling (1–50 covers), cost calculations, and two-column adapted recipe view (Ingredients FIRST, cooking SOPs SECOND).

---

## How We Use FoodoScope Data

| Endpoint | Why |
|---|---|
| `GET /recipe2-api/recipeDB/recipes/search` | Search and retrieve benchmark recipes across regional cuisines for substitution analysis |
| `GET /recipe2-api/recipeDB/recipe/{id}` | Ingest detailed recipe bill of ingredients, categories, and cooking instructions |
| `GET /flavordb-api/flavordb/molecules` | Extract flavor chemical profile vectors for candidate substitute ingredients |
| `GET /flavordb-api/flavordb/entity/{id}` | Pairwise compound co-occurrence calculations to predict culinary synergy |

---

## Architecture

```
[ Browser / Mobile Device ]
            │
            ▼
┌────────────────────────────────────────────────────────┐
│  FlavorShift AI Frontend SPA (Vanilla JS + Modern CSS) │
│  - Swap Lab & Interactive Ratio Converter              │
│  - Human Taste Validation (HTV) Hub                    │
│  - Recipe Explorer & Two-Column Adapted View           │
└───────────┬────────────────────────────────────────────┘
            │
            ├──────────────────────────────────────────┐
            ▼                                          ▼
┌───────────────────────────────┐     ┌─────────────────────────────────┐
│ FastAPI Intelligence Backend  │     │ Node.js FoodoScope Proxy Server │
│ - Mathematical Scoring Engine │     │ - CORS Management               │
│ - Allergen / Dietary Gates    │     │ - Rate-limiting Cache           │
│ - Rheology & Moisture Scaling │     └────────────────┬────────────────┘
└───────────┬───────────────────┘                      │
            │                                          │
            └──────────────────┬───────────────────────┘
                               ▼
            ┌──────────────────────────────────────────┐
            │       FoodoScope API Gateway             │
            │   (RecipeDB · FlavorDB · IIIT-Delhi)     │
            └──────────────────────────────────────────┘
```

---

## Run It Locally

### Option 1: Frontend SPA (Zero Setup)
Open `index.html` directly in your browser, or run a local HTTP server:
```bash
# Python
python -m http.server 8080

# Or Node.js
npx serve .
```
Visit `http://localhost:8080/`.

### Option 2: Full Stack (FastAPI Backend + FoodoScope Proxy)
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and paste your FoodoScope API key

# 2. Start FoodoScope Proxy
node server/foodoscope-proxy.mjs

# 3. Start Python Intelligence Backend
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Run Test Suite
```bash
# Backend pytest suite
python -m pytest backend/tests/test_intelligent_substitution.py -v
```

---

## What's Next

- **Sensory Rheology Model (ONNX)**: On-device texture prediction model using ingredient viscosity and fat droplet dispersion parameters.
- **Computer Vision Plate Inspection**: Photo verification of substitute dish emulsion stability using edge ML.
- **Multilingual Regional Voice Support**: Voice-guided kitchen assistant in Hindi, Tamil, Telugu, and Bengali for local cooks.

---

## Acknowledgements

- Data from the **[FoodoScope](https://cosylab.iiitd.edu.in)** APIs (RecipeDB, FlavorDB) developed by the Complex Systems Lab, IIIT-Delhi.
- Built for **Fork-IT 2026** · ESYA'26 · IIIT-Delhi · 14–15 Nov 2026.
- Team: **t46 · TechTadka**

---
<sub>Starter docs & references: [`docs/STARTER_GUIDE.md`](docs/STARTER_GUIDE.md) · Architecture: [`docs/FLAVORSHIFT_AI_ARCHITECTURE.md`](docs/FLAVORSHIFT_AI_ARCHITECTURE.md)</sub>
