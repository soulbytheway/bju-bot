import base64
import json
import urllib.parse

import httpx

from config import settings

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.5-flash-lite:generateContent"
)

RECOGNITION_PROMPT = """
Проаналізуй фото їжі. Визнач всі страви/продукти на тарілці, оціни приблизну
вагу кожного компонента в грамах (враховуючи візуальний розмір порції), і
оціни харчову цінність (білки/жири/вуглеводи/калорії) для цієї ваги на основі
типових значень для такого продукту.

Поверни ЛИШЕ JSON без жодного додаткового тексту, у форматі:
{
  "items": [
    {
      "name": "назва страви українською",
      "weight_g": число,
      "protein": число (грам),
      "fat": число (грам),
      "carbs": число (грам),
      "kcal": число
    }
  ],
  "is_food": true
}

Якщо на фото немає їжі - поверни "is_food": false і порожній список items.
"""


async def _call_gemini_raw(parts: list) -> str:
    """Спільна логіка виклику Gemini - повертає сирий текст відповіді, без парсингу."""
    payload = {"contents": [{"parts": parts}]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GEMINI_URL}?key={settings.gemini_api_key}",
            json=payload,
        )

    if response.status_code != 200:
        raise RuntimeError(f"Gemini API помилка {response.status_code}: {response.text}")

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


async def _call_gemini(parts: list) -> dict:
    raw_text = await _call_gemini_raw(parts)
    return _parse_json_response(raw_text)


async def recognize_food_from_photo(photo_bytes: bytes) -> dict:
    image_b64 = base64.b64encode(photo_bytes).decode("utf-8")
    parts = [
        {"text": RECOGNITION_PROMPT},
        {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
    ]
    return await _call_gemini(parts)


async def generate_json_response(prompt: str) -> dict:
    return await _call_gemini([{"text": prompt}])


async def generate_text_response(prompt: str) -> str:
    """Для випадків, коли потрібна звичайна текстова відповідь, а не JSON (наприклад AI-порада)."""
    raw_text = await _call_gemini_raw([{"text": prompt}])
    return raw_text.strip()


def _parse_json_response(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Не вдалось розпарсити відповідь Gemini як JSON: {e}\nВідповідь: {raw_text}")


def youtube_search_url(dish_name: str) -> str:
    query = urllib.parse.quote(f"рецепт {dish_name}")
    return f"https://www.youtube.com/results?search_query={query}"