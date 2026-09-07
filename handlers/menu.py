from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from db.database import ensure_user_exists, get_today_totals, get_profile, delete_user_data
from keyboards.reply import main_menu_keyboard
from keyboards.inline import add_food_choice_keyboard, settings_keyboard, confirm_delete_keyboard
from services.profile import calculate_daily_norm

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    ensure_user_exists(message.from_user.id)
    await message.answer(
        "Привіт! 👋 Я аналізую їжу і рахую БЖУ.\n\n"
        "Надішли фото страви або опиши текстом, що з'їв.\n\n"
        "Радив би спочатку заповнити профіль (кнопка 👤 Профіль) - "
        "тоді я зможу показувати не просто цифри, а прогрес відносно твоєї денної норми.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "📸 Додати їжу")
async def prompt_add_food(message: Message) -> None:
    await message.answer(
        "📸 Надішли фото страви прямо в цей чат, або опиши текстом:",
        reply_markup=add_food_choice_keyboard(),
    )


@router.message(F.text == "📊 Сьогодні")
async def show_today(message: Message) -> None:
    totals = get_today_totals(message.from_user.id)
    profile = get_profile(message.from_user.id)

    if not profile.is_complete():
        await message.answer(
            "📊 З'їдено сьогодні:\n"
            f"Білки: {totals['protein']:g}г | Жири: {totals['fat']:g}г | "
            f"Вуглеводи: {totals['carbs']:g}г\n"
            f"Калорії: ~{totals['kcal']:g} ккал\n\n"
            "💡 Заповни профіль (👤 Профіль), щоб бачити прогрес відносно денної норми."
        )
        return

    norm = calculate_daily_norm(profile)
    kcal_left = norm.kcal - totals["kcal"]
    protein_left = norm.protein - totals["protein"]
    fat_left = norm.fat - totals["fat"]
    carbs_left = norm.carbs - totals["carbs"]

    await message.answer(
        "📊 Сьогодні:\n\n"
        f"З'їдено: {totals['kcal']:g} / {norm.kcal:g} ккал\n"
        f"Білки: {totals['protein']:g}г / {norm.protein:g}г\n"
        f"Жири: {totals['fat']:g}г / {norm.fat:g}г\n"
        f"Вуглеводи: {totals['carbs']:g}г / {norm.carbs:g}г\n\n"
        f"🎯 Залишилось до норми: ~{max(kcal_left, 0):g} ккал "
        f"(білки {max(protein_left, 0):g}г, жири {max(fat_left, 0):g}г, "
        f"вуглеводи {max(carbs_left, 0):g}г)"
    )


@router.message(F.text == "⚙️ Налаштування")
async def show_settings(message: Message) -> None:
    await message.answer("⚙️ Налаштування", reply_markup=settings_keyboard())


@router.callback_query(F.data == "settings_delete_data")
async def handle_delete_request(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "⚠️ Це видалить усі твої дані назавжди: профіль, історію їжі.\n"
        "Впевнений?",
        reply_markup=confirm_delete_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "settings_delete_confirm")
async def handle_delete_confirm(callback: CallbackQuery) -> None:
    delete_user_data(callback.from_user.id)
    await callback.message.edit_text(
        "✅ Всі твої дані видалено. Напиши /start, щоб почати заново."
    )
    await callback.answer()


@router.callback_query(F.data == "settings_delete_cancel")
async def handle_delete_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Скасовано, дані на місці.")
    await callback.answer()