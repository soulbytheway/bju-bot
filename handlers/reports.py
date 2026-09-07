from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile

from db.database import get_profile
from services.profile import calculate_daily_norm
from services.report import generate_weekly_chart

router = Router()

@router.message(F.text == "📈 Звіти")
async def show_weekly_report(message: Message) -> None:
    profile = get_profile(message.from_user.id)
    norm_kcal = None
    if profile.is_complete():
        norm = calculate_daily_norm(profile)
        norm_kcal = norm.kcal

    thinking_msg = await message.answer("📊 Будую графік...")

    try:
        chart_bytes = generate_weekly_chart(message.from_user.id, norm_kcal)
    except Exception as e:
        print(f"[ERROR] Weekly chart generation failed: {type(e).__name__}: {e}")
        await thinking_msg.edit_text("⚠️ Не вдалось побудувати графік. Спробуй ще раз.")
        return

    await thinking_msg.delete()

    photo = BufferedInputFile(chart_bytes, filename="weekly_report.png")
    await message.answer_photo(photo, caption="📈 Твоє споживання калорій за останні 7 днів")