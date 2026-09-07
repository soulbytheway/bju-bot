from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from db.database import save_meal, get_profile, get_today_totals
from db.schemas import MealAnalysis
from keyboards.inline import meal_confirmation_keyboard
from services.nutrition import (
    analyze_food_photo, analyze_food_text, format_meal_response, generate_meal_advice,
)
from services.profile import calculate_daily_norm
from services.checks import is_valid_text_input, clean_and_truncate
from states import MealStates

router = Router()


async def _build_budget_context(user_id: int) -> str:
    profile = get_profile(user_id)
    if not profile.is_complete():
        return ""

    norm = calculate_daily_norm(profile)
    totals = get_today_totals(user_id)
    kcal_left = max(norm.kcal - totals["kcal"], 0)
    return f"Залишок денного бюджету калорій до цього прийому їжі: ~{kcal_left:.0f} ккал."


async def _present_analysis_for_confirmation(message: Message, state: FSMContext, analysis: MealAnalysis) -> None:
    if not analysis.is_food:
        await message.answer(format_meal_response(analysis))
        await state.clear()
        return

    await state.update_data(analysis=analysis)
    await state.set_state(MealStates.waiting_confirmation)

    response_text = format_meal_response(analysis)

    try:
        budget_context = await _build_budget_context(message.chat.id)
        advice = await generate_meal_advice(analysis, budget_context)
        if advice:
            response_text += f"\n\n💡 {advice}"
    except Exception as e:
        print(f"[WARNING] AI advice generation failed: {type(e).__name__}: {e}")

    await message.answer(response_text, reply_markup=meal_confirmation_keyboard())


@router.message(F.photo)
async def handle_food_photo(message: Message, bot: Bot, state: FSMContext) -> None:
    thinking_msg = await message.answer("🔍 Аналізую фото...")

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_bytes = await bot.download_file(file.file_path)

    try:
        analysis = await analyze_food_photo(photo_bytes.read())
    except Exception as e:
        print(f"[ERROR] Gemini recognition failed: {type(e).__name__}: {e}")
        await thinking_msg.edit_text("⚠️ Не вдалось проаналізувати фото. Спробуй ще раз за хвилину.")
        return

    await thinking_msg.delete()
    await _present_analysis_for_confirmation(message, state, analysis)


@router.callback_query(F.data == "meal_text_input")
async def handle_text_input_request(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Опиши, що з'їв, наприклад: куряче філе 150г, гречка 100г, огірок 50г"
    )
    await state.set_state(MealStates.waiting_text_description)
    await callback.answer()


@router.message(MealStates.waiting_text_description)
async def handle_text_description(message: Message, state: FSMContext) -> None:
    if not is_valid_text_input(message.text):
        await message.answer("Напиши текстом, що з'їв, наприклад: куряче філе 150г")
        return

    description = clean_and_truncate(message.text)
    thinking_msg = await message.answer("🔍 Аналізую...")

    try:
        analysis = await analyze_food_text(description)
    except Exception as e:
        print(f"[ERROR] Text meal analysis failed: {type(e).__name__}: {e}")
        await thinking_msg.edit_text("⚠️ Не вдалось проаналізувати опис. Спробуй ще раз.")
        return

    await thinking_msg.delete()
    await _present_analysis_for_confirmation(message, state, analysis)


@router.callback_query(F.data == "meal_confirm", MealStates.waiting_confirmation)
async def handle_meal_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    analysis: MealAnalysis = data["analysis"]

    save_meal(callback.from_user.id, analysis)
    await state.clear()

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Збережено в сьогоднішні прийоми їжі!",
        reply_markup=None,
    )
    await callback.answer()


@router.callback_query(F.data == "meal_correct", MealStates.waiting_confirmation)
async def handle_meal_correct(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Опиши, що насправді там було, наприклад: куряче філе 150г, гречка 100г, огірок 50г"
    )
    await state.set_state(MealStates.waiting_correction_text)
    await callback.answer()


@router.message(MealStates.waiting_correction_text)
async def handle_correction_text(message: Message, state: FSMContext) -> None:
    if not is_valid_text_input(message.text):
        await message.answer("Напиши текстом, що насправді там було")
        return

    description = clean_and_truncate(message.text)
    thinking_msg = await message.answer("🔍 Переаналізовую...")

    try:
        analysis = await analyze_food_text(description)
    except Exception as e:
        print(f"[ERROR] Correction analysis failed: {type(e).__name__}: {e}")
        await thinking_msg.edit_text("⚠️ Не вдалось проаналізувати. Спробуй ще раз.")
        return

    await thinking_msg.delete()
    await _present_analysis_for_confirmation(message, state, analysis)


@router.callback_query(F.data == "meal_cancel", MealStates.waiting_confirmation)
async def handle_meal_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Скасовано")