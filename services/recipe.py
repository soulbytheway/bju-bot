import random

from db.schemas import UserProfile
from external.ai_client import generate_json_response, youtube_search_url
from external.youtube_client import find_recipe_video_url

CATEGORY_LABELS = {
    "breakfast": "сніданок",
    "lunch": "обід",
    "dinner": "вечеря",
    "snack": "перекус",
}

CATEGORY_RANGES = {
    "breakfast": (300, 600),
    "lunch": (500, 900),
    "dinner": (400, 700),
    "snack": (100, 300),
}

CUISINE_HINTS = [
    "українська кухня", "середземноморська кухня", "азійська кухня",
    "проста хатня їжа", "фітнес-кухня з акцентом на білок", "вегетаріанська кухня",
]

RECIPE_SUGGESTION_PROMPT = """
Запропонуй один конкретний рецепт для прийому їжі категорії: {category_label}.

Типова калорійність такого прийому їжі: {range_min}-{range_max} ккал.
У людини залишилось на сьогодні: ~{kcal:.0f} ккал, білки ~{protein:.0f}г,
жири ~{fat:.0f}г, вуглеводи ~{carbs:.0f}г.

ВАЖЛИВО: НЕ намагайся використати весь залишок бюджету одразу. Запропонуй
реалістичну порцію саме для категорії {category_label}, що вписується в
типовий діапазон {range_min}-{range_max} ккал і не перевищує залишок дня.

Уникай найбанальніших очевидних варіантів (типу "куряче філе з гречкою" за
замовчуванням) - спробуй запропонувати щось у стилі: {cuisine_hint}, якщо це
підходить під калорійність і категорію. Кожна пропозиція має бути різною.
{allergy_note}

Це має бути реальна, конкретна страва, яку можна приготувати вдома зі
звичайних продуктів, розрахована на 1 порцію.

Поверни ЛИШЕ JSON без жодного додаткового тексту:
{{
  "name": "назва страви українською",
  "ingredients": ["інгредієнт 1 - кількість", "інгредієнт 2 - кількість"],
  "instructions": "короткий покроковий рецепт, 3-5 речень",
  "protein": число,
  "fat": число,
  "carbs": число,
  "kcal": число
}}
"""

DISH_ANALYSIS_PROMPT = """
Користувач хоче приготувати страву: "{dish_name}".
Запропонуй один типовий рецепт цієї страви на одну порцію та оціни харчову цінність.
{allergy_note}

Поверни ЛИШЕ JSON без жодного додаткового тексту:
{{
  "name": "назва страви українською",
  "ingredients": ["інгредієнт 1 - кількість", "інгредієнт 2 - кількість"],
  "instructions": "короткий покроковий рецепт, 3-5 речень",
  "protein": число,
  "fat": число,
  "carbs": число,
  "kcal": число
}}
"""


def _build_allergy_note(allergies: str | None) -> str:
    if not allergies or allergies.strip().lower() in ("немає", "нема", "-", ""):
        return ""
    return f"ВАЖЛИВО: уникай продуктів, на які в користувача алергія/непереносимість: {allergies}."


async def suggest_recipe_for_budget(
    category: str, kcal: float, protein: float, fat: float, carbs: float, profile: UserProfile
) -> dict:
    range_min, range_max = CATEGORY_RANGES[category]
    prompt = RECIPE_SUGGESTION_PROMPT.format(
        category_label=CATEGORY_LABELS[category],
        range_min=range_min,
        range_max=range_max,
        kcal=kcal,
        protein=protein,
        fat=fat,
        carbs=carbs,
        cuisine_hint=random.choice(CUISINE_HINTS),
        allergy_note=_build_allergy_note(profile.allergies),
    )
    return await generate_json_response(prompt)


async def analyze_dish_by_name(dish_name: str, profile: UserProfile) -> dict:
    prompt = DISH_ANALYSIS_PROMPT.format(
        dish_name=dish_name,
        allergy_note=_build_allergy_note(profile.allergies),
    )
    return await generate_json_response(prompt)


def format_recipe_message(recipe: dict) -> str:
    lines = [f"🍽 {recipe['name']}", "", "Інгредієнти:"]
    for ing in recipe.get("ingredients", []):
        lines.append(f"• {ing}")
    lines.append("")
    lines.append("Приготування:")
    lines.append(recipe.get("instructions", ""))
    lines.append("")
    lines.append(
        f"📊 БЖУ: Білки {recipe.get('protein', 0):g}г | Жири {recipe.get('fat', 0):g}г | "
        f"Вуглеводи {recipe.get('carbs', 0):g}г | Калорії ~{recipe.get('kcal', 0):g} ккал"
    )
    return "\n".join(lines)


async def get_video_url(recipe: dict) -> str:
    real_video_url = await find_recipe_video_url(recipe["name"])
    if real_video_url:
        return real_video_url
    return youtube_search_url(recipe["name"])