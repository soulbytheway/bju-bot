import httpx

from config import settings

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


async def find_recipe_video_url(dish_name: str) -> str | None:
    params = {
        "part": "snippet",
        "q": f"рецепт {dish_name}",
        "type": "video",
        "maxResults": 1,
        "key": settings.youtube_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(YOUTUBE_SEARCH_URL, params=params)

        if response.status_code != 200:
            print(f"[WARNING] YouTube API помилка {response.status_code}: {response.text}")
            return None

        data = response.json()
        items = data.get("items", [])
        if not items:
            return None

        video_id = items[0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"

    except Exception as e:
        print(f"[WARNING] YouTube search failed: {type(e).__name__}: {e}")
        return None