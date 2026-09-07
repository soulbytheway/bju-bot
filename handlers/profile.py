from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from db.database import get_profile, update_profile_field
from keyboards.inline import (
    gender_keyboard, activity_keyboard, goal_keyboard,
    profile_edit_keyboard, profile_view_keyboard,
)
from services.profile import calculate_daily_norm
from states import ProfileStates

router = Router()

ACTIVITY_LABELS = {"low": "Низька", "medium": "Середня", "high": "Висока"}
GOAL_LABELS = {"lose": "Схуднення", "maintain": "Підтримка ваги", "gain": "Набір маси"}
GENDER_LABELS = {"male": "Чоловіча", "female": "Жіноча"}


def _format_profile_summary(profile) -> str:
    norm = calculate_daily_norm(profile)
    allergies_line = profile.allergies if profile.allergies else "не вказано"
    return (
        f"👤 Твій профіль:\n"
        f"Стать: {GENDER_LABELS[profile.gender]}\n"
        f"Вік: {profile.age}\n"
        f"Вага: {profile.weight:g} кг\n"
        f"Зріст: {profile.height:g} см\n"
        f"Активність: {ACTIVITY_LABELS[profile.activity]}\n"
        f"Ціль: {GOAL_LABELS[profile.goal]}\n"
        f"Алергії: {allergies_line}\n\n"
        f"🎯 Денна норма:\n"
        f"Калорії: ~{norm.kcal} ккал\n"
        f"Білки: {norm.protein:g}г | Жири: {norm.fat:g}г | Вуглеводи: {norm.carbs:g}г"
    )


@router.message(Command("profile"))
@router.message(F.text == "👤 Профіль")
async def show_profile(message: Message, state: FSMContext) -> None:
    profile = get_profile(message.from_user.id)

    if not profile.is_complete():
        await state.update_data(editing=False)
        await message.answer(
            "Профіль ще не заповнений. Давай заповнимо - це займе хвилину.\n\n"
            "Яка в тебе стать?",
            reply_markup=gender_keyboard(),
        )
        await state.set_state(ProfileStates.waiting_gender)
        return

    await message.answer(
        _format_profile_summary(profile),
        reply_markup=profile_view_keyboard(),
    )


@router.callback_query(F.data == "profile_edit_menu")
async def show_edit_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Що хочеш змінити?",
        reply_markup=profile_edit_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "edit_weight")
async def start_edit_weight(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(editing=True)
    await callback.message.edit_text("Яка твоя нова вага в кг? (наприклад: 75 або 75.5)")
    await state.set_state(ProfileStates.waiting_weight)
    await callback.answer()


@router.callback_query(F.data == "edit_height")
async def start_edit_height(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(editing=True)
    await callback.message.edit_text("Який твій новий зріст в см? (наприклад: 178)")
    await state.set_state(ProfileStates.waiting_height)
    await callback.answer()


@router.callback_query(F.data == "edit_activity")
async def start_edit_activity(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(editing=True)
    await callback.message.edit_text("Новий рівень активності?", reply_markup=activity_keyboard(show_back=True))
    await state.set_state(ProfileStates.waiting_activity)
    await callback.answer()


@router.callback_query(F.data == "edit_goal")
async def start_edit_goal(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(editing=True)
    await callback.message.edit_text("Нова ціль?", reply_markup=goal_keyboard(show_back=True))
    await state.set_state(ProfileStates.waiting_goal)
    await callback.answer()


@router.callback_query(F.data == "edit_birth_year")
async def start_edit_birth_year(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(editing=True)
    await callback.message.edit_text("Якого ти року народження? (наприклад: 2005)")
    await state.set_state(ProfileStates.waiting_birth_year)
    await callback.answer()


@router.callback_query(F.data == "edit_allergies")
async def start_edit_allergies(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(editing=True)
    await callback.message.edit_text(
        "На що в тебе алергія чи харчові обмеження? Напиши через кому, "
        "або 'немає', якщо нема жодних обмежень."
    )
    await state.set_state(ProfileStates.waiting_allergies)
    await callback.answer()


async def _finish_field_update(message: Message, state: FSMContext, user_id: int) -> bool:
    data = await state.get_data()
    if data.get("editing"):
        await state.clear()
        profile = get_profile(user_id)
        await message.answer(_format_profile_summary(profile), reply_markup=profile_view_keyboard())
        return True
    return False


@router.callback_query(F.data.startswith("gender_"), ProfileStates.waiting_gender)
async def handle_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.removeprefix("gender_")
    update_profile_field(callback.from_user.id, "gender", gender)

    if await _finish_field_update(callback.message, state, callback.from_user.id):
        await callback.answer()
        return

    await callback.message.edit_text("Якого ти року народження? (наприклад: 2005)")
    await state.set_state(ProfileStates.waiting_birth_year)
    await callback.answer()


@router.message(ProfileStates.waiting_birth_year)
async def handle_birth_year(message: Message, state: FSMContext) -> None:
    from datetime import date

    try:
        birth_year = int(message.text)
        age = date.today().year - birth_year
        if not (10 <= age <= 100):
            raise ValueError
    except ValueError:
        await message.answer("Введи рік народження числом, наприклад: 2005")
        return

    update_profile_field(message.from_user.id, "birth_year", birth_year)

    if await _finish_field_update(message, state, message.from_user.id):
        return

    await message.answer("Яка твоя вага в кг? (наприклад: 75 або 75.5)")
    await state.set_state(ProfileStates.waiting_weight)


@router.message(ProfileStates.waiting_weight)
async def handle_weight(message: Message, state: FSMContext) -> None:
    try:
        weight = float(message.text.replace(",", "."))
        if not (30 <= weight <= 300):
            raise ValueError
    except ValueError:
        await message.answer("Введи вагу числом у кг, наприклад: 75")
        return

    update_profile_field(message.from_user.id, "weight", weight)

    if await _finish_field_update(message, state, message.from_user.id):
        return

    await message.answer("Який твій зріст в см? (наприклад: 178)")
    await state.set_state(ProfileStates.waiting_height)


@router.message(ProfileStates.waiting_height)
async def handle_height(message: Message, state: FSMContext) -> None:
    try:
        height = float(message.text.replace(",", "."))
        if not (100 <= height <= 250):
            raise ValueError
    except ValueError:
        await message.answer("Введи зріст числом у см, наприклад: 178")
        return

    update_profile_field(message.from_user.id, "height", height)

    if await _finish_field_update(message, state, message.from_user.id):
        return

    await message.answer("Який у тебе рівень фізичної активності?", reply_markup=activity_keyboard())
    await state.set_state(ProfileStates.waiting_activity)


@router.callback_query(F.data.startswith("activity_"), ProfileStates.waiting_activity)
async def handle_activity(callback: CallbackQuery, state: FSMContext) -> None:
    activity = callback.data.removeprefix("activity_")
    update_profile_field(callback.from_user.id, "activity", activity)

    if await _finish_field_update(callback.message, state, callback.from_user.id):
        await callback.answer()
        return

    await callback.message.edit_text("Яка твоя ціль?", reply_markup=goal_keyboard())
    await state.set_state(ProfileStates.waiting_goal)
    await callback.answer()


@router.callback_query(F.data.startswith("goal_"), ProfileStates.waiting_goal)
async def handle_goal(callback: CallbackQuery, state: FSMContext) -> None:
    goal = callback.data.removeprefix("goal_")
    update_profile_field(callback.from_user.id, "goal", goal)

    if await _finish_field_update(callback.message, state, callback.from_user.id):
        await callback.answer()
        return

    await callback.message.edit_text(
        "На що в тебе алергія чи харчові обмеження? Напиши через кому, "
        "або 'немає', якщо нема жодних обмежень."
    )
    await state.set_state(ProfileStates.waiting_allergies)
    await callback.answer()


@router.message(ProfileStates.waiting_allergies)
async def handle_allergies(message: Message, state: FSMContext) -> None:
    update_profile_field(message.from_user.id, "allergies", message.text)
    await state.clear()

    profile = get_profile(message.from_user.id)
    norm = calculate_daily_norm(profile)

    await message.answer(
        f"✅ Профіль заповнено!\n\n"
        f"🎯 Твоя денна норма:\n"
        f"Калорії: ~{norm.kcal} ккал\n"
        f"Білки: {norm.protein:g}г | Жири: {norm.fat:g}г | Вуглеводи: {norm.carbs:g}г\n\n"
        f"Тепер команда 'Сьогодні' показуватиме прогрес відносно цієї норми, "
        f"а рецепти автоматично враховуватимуть твої алергії."
    )