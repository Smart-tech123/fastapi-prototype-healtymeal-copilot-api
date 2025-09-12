# 📝 Documentation & Docstrings

This project follows a **docstring-first philosophy** to ensure APIs, models, and endpoints are **self-documenting**, **discoverable**, and generate clean **OpenAPI / Swagger docs**.

We use **Python docstrings (PEP 257)** along with **FastAPI**’s automatic doc rendering.

---

## ✅ Docstring Guidelines

- Use **triple-quoted strings (`"""`)** right under class/function definitions.  
- Write **clear, concise summaries** in the first line.  
- Use **Google-style or reST-style** docstrings (must be consistent). This repo follows **Google-style**.  
- For **models**, describe each field in the class docstring.  
- For **endpoints**, include:
  * **Summary line** (auto-appears in OpenAPI docs)  
  * Description of **parameters, responses, errors, and use cases**  

---

## 📌 Example: Pydantic Model Docstring

```python
from pydantic import BaseModel, Field

class MealRequest(BaseModel):
    """Request schema for generating a meal plan.

    Attributes:
        user_id: Unique identifier of the requesting user.
        dietary_preferences: List of dietary considerations (e.g., vegan, keto).
        excluded_ingredients: List of ingredients to avoid (e.g., peanuts, gluten).
        meals_per_day: Number of meals per day to generate.
        days: Number of days for the meal plan.
    """

    user_id: str = Field(..., example="user_123")
    dietary_preferences: list[str] = Field(default_factory=list, example=["vegan"])
    excluded_ingredients: list[str] = Field(default_factory=list, example=["gluten"])
    meals_per_day: int = Field(default=3, ge=1, le=6, example=3)
    days: int = Field(default=7, ge=1, le=30, example=7)
```

👉 Why this works:
- Clear docstring at **class level**  
- Per-field metadata (`example`, `ge`, `le`) improves **Swagger docs** and validation  

---

## 📌 Example: Endpoint Docstring

```python
from fastapi import APIRouter, Depends
from .models import MealRequest
from .schemas import MealPlanResponse

router = APIRouter()

@router.post("/meal-plan", response_model=MealPlanResponse, summary="Generate meal plan")
async def generate_meal_plan(request: MealRequest):
    """Generate a personalized meal plan for a user.

    This endpoint uses user preferences, dietary restrictions, and exclusions
    to generate a multi-day meal plan. The generation leverages LLMs and
    vector similarity search against stored meal recipes.

    Args:
        request: MealRequest Pydantic model containing meal preferences.

    Returns:
        MealPlanResponse: A complete multi-day meal plan including meals per day.

    Raises:
        HTTPException 400: If validation fails.
        HTTPException 500: If the AI service is unavailable.
    """
    return await some_meal_service.generate(request)
```

👉 Why this works:
- Short `summary` for OpenAPI  
- Detailed docstring for **developers/users**  
- Explains **args, return values, and errors**  

---

## 📌 Example: Service Function Docstring

```python
async def fetch_recipe_embeddings(meal_name: str) -> list[float]:
    """Fetch vector embeddings for a given meal name.

    Args:
        meal_name: The textual name/description of the meal.

    Returns:
        A list of floats representing the semantic embedding of the meal.

    Raises:
        RuntimeError: If embedding service is unavailable.
    """
    ...
```

---

## 🚦 Docstring in Development Workflow

To enforce docstring quality:

1. **Linting with Ruff**  
   Configure rule `D1` (pydocstyle) to enforce docstring requirements. Example in `pyproject.toml`:
   ```toml
   [tool.ruff.lint]
   select = ["E", "F", "D"]
   ignore = ["D203", "D213"]  # relax rules we don’t care about
   ```

2. **Testing docstrings (optional)**  
   You can add [`interrogate`](https://interrogate.readthedocs.io/en/latest/) or `pytest --doctest-modules` for stricter enforcement.

3. **Pull Request Checklist**  
   - ✅ Function and class docstrings present  
   - ✅ Models describe all fields  
   - ✅ Endpoints have summary, description, args/returns  

---

## 🔑 Benefits

- Automatic **API documentation** with FastAPI  
- Self-documenting models and services  
- Easier onboarding for contributors  
- Higher API usability for integrators  