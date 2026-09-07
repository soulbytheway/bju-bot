from external.ai_client import recognize_food_from_photo, generate_json_response, generate_text_response
from db.schemas import FoodItem, MealAnalysis

TEXT_MEAL_PROMPT = """
Користувач описав, що з'їв: "{description}"

Визнач всі страви/продукти, оціни вагу кожного компонента в грамах (якщо
користувач вказав вагу явно - використай її; якщо ні - оціни типову порцію),
і оціни харчову цінність (білки/жири/вуглеводи/калорії).

Поверни ЛИШЕ JSON без жодного додаткового тексту, у форматі:
{{
  "items": [
    {{
      "name": "назва страви українською",
      "weight_g": число,
      "protein": число,
      "fat": число,
      "carbs": число,
      "kcal": число
    }}
  ],
  "is_food": true
}}

Якщо опис не про їжу - поверни "is_food": false і порожній список items.
"""

ADVICE_PROMPT = """
Прийом їжі: {items_summary}.
Сумарно: {kcal:.0f} ккал, білки {protein:.0f}г, жири {fat:.0f}г, вуглеводи {carbs:.0f}г.
{budget_context}

Дай ОДНУ коротку пораду щодо САМЕ ЦІЄЇ страви, максимум 15 слів, українською.

Якщо в страві справді бракує чогось конкретного (наприклад, мало білка,
забагато жиру чи вуглеводів) - вкажи саме це.
Якщо страва дійсно збалансована - похвали конкретно ЧОМУ саме вона
збалансована (наприклад, за яким співвідношенням БЖУ), а не просто
загальною фразою.

НЕ використовуй шаблонні фрази на кшталт "смакуй на здоров'я",
"чудовий вибір" без пояснення чому - завжди давай конкретну причину.
"""


async def analyze_food_photo(photo_bytes: bytes) -> MealAnalysis:
    raw = await recognize_food_from_photo(photo_bytes)
    return _build_analysis_from_raw(raw)


async def analyze_food_text(description: str) -> MealAnalysis:
    raw = await generate_json_response(TEXT_MEAL_PROMPT.format(description=description))
    return _build_analysis_from_raw(raw)


def _build_analysis_from_raw(raw: dict) -> MealAnalysis:
    if not raw.get("is_food", False):
        return MealAnalysis(items=[], is_food=False)

    items = [
        FoodItem(
            name=item["name"],
            weight_g=item["weight_g"],
            protein=item.get("protein", 0),
            fat=item.get("fat", 0),
            carbs=item.get("carbs", 0),
            kcal=item.get("kcal", 0),
        )
        for item in raw.get("items", [])
    ]

    return _calculate_totals(items)


def _calculate_totals(items: list[FoodItem]) -> MealAnalysis:
    return MealAnalysis(
        items=items,
        is_food=True,
        total_protein=round(sum(i.protein for i in items), 1),
        total_fat=round(sum(i.fat for i in items), 1),
        total_carbs=round(sum(i.carbs for i in items), 1),
        total_kcal=round(sum(i.kcal for i in items), 1),
    )


async def generate_meal_advice(analysis: MealAnalysis, budget_context: str = "") -> str:
    items_summary = ", ".join(f"{i.name} ({i.weight_g:g}г)" for i in analysis.items)
    prompt = ADVICE_PROMPT.format(
        items_summary=items_summary,
        kcal=analysis.total_kcal,
        protein=analysis.total_protein,
        fat=analysis.total_fat,
        carbs=analysis.total_carbs,
        budget_context=budget_context,
    )
    return await generate_text_response(prompt)


def format_meal_response(analysis: MealAnalysis) -> str:
    if not analysis.is_food:
        return "🤔 Не бачу тут їжі. Спробуй ще раз чіткіше описати або сфотографувати страву."

    lines = ["🍽 Розпізнано:"]
    for item in analysis.items:
        lines.append(f"• {item.name} — {item.weight_g:g}г")

    lines.append("")
    lines.append("📊 БЖУ (сумарно):")
    lines.append(
        f"Білки: {analysis.total_protein:g}г | "
        f"Жири: {analysis.total_fat:g}г | "
        f"Вуглеводи: {analysis.total_carbs:g}г"
    )
    lines.append(f"Калорії: ~{analysis.total_kcal:g} ккал")

    return "\n".join(lines)