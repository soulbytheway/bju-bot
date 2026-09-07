from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from db.database import get_profile, get_today_totals, save_meal
from db.schemas import FoodItem, MealAnalysis
from keyboards.inline import recipe_choice_keyboard, recipe_result_keyboard, meal_category_keyboard
from services.profile import calculate_daily_norm
from services.recipe import suggest_recipe_for_budget, analyze_dish_by_name, format_recipe_message, get_video_url
from services.checks import is_valid_text_input, clean_and_truncate
from states import RecipeStates

router = Router()


async def _send_recipe_result(message: Message, state: FSMContext, recipe: dict) -> None:
    await state.update_data(recipe=recipe)
    video_url = await get_video_url(recipe)

    await message.answer(
        format_recipe_message(recipe),
        reply_markup=recipe_result_keyboard(video_url),
    )
    await message.answer(f"🎬 Відео-рецепт:\n{video_url}")


@router.message(F.text == "🍽 Що приготувати")
async def show_recipe_menu(message: Message) -> None:
    await message.answer("Як підібрати рецепт?", reply_markup=recipe_choice_keyboard())


@router.callback_query(F.data == "recipe_menu_back")
async def handle_recipe_menu_back(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Як підібрати рецепт?", reply_markup=recipe_choice_keyboard())
    await callback.answer()


@router.callback_query(F.data == "recipe_suggest")
async def handle_recipe_suggest(callback: CallbackQuery) -> None:
    profile = get_profile(callback.from_user.id)

    if not profile.is_complete():
        await callback.message.edit_text(
            "Для цього потрібен заповнений профіль (щоб знати твою денну норму). "
            "Заповни його через 👤 Профіль і спробуй ще раз."
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "На який прийом їжі підбираємо рецепт?",
        reply_markup=meal_category_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_"))
async def handle_category_selected(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.removeprefix("category_")

    profile = get_profile(callback.from_user.id)
    norm = calculate_daily_norm(profile)
    totals = get_today_totals(callback.from_user.id)

    kcal_left = max(norm.kcal - totals["kcal"], 0)
    protein_left = max(norm.protein - totals["protein"], 0)
    fat_left = max(norm.fat - totals["fat"], 0)
    carbs_left = max(norm.carbs - totals["carbs"], 0)

    await callback.message.edit_text("🔍 Підбираю рецепт...")

    try:
        recipe = await suggest_recipe_for_budget(category, kcal_left, protein_left, fat_left, carbs_left, profile)
    except Exception as e:
        print(f"[ERROR] Recipe suggestion failed: {type(e).__name__}: {e}")
        await callback.message.edit_text("⚠️ Не вдалось підібрати рецепт. Спробуй ще раз за хвилину.")
        await callback.answer()
        return

    await _send_recipe_result(callback.message, state, recipe)
    await callback.answer()


@router.callback_query(F.data == "recipe_by_name")
async def handle_recipe_by_name_request(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Яку страву хочеш приготувати? Напиши назву, наприклад: омлет з сиром")
    await state.set_state(RecipeStates.waiting_dish_name)
    await callback.answer()


@router.message(RecipeStates.waiting_dish_name)
async def handle_dish_name(message: Message, state: FSMContext) -> None:
    if not is_valid_text_input(message.text):
        await message.answer("Напиши назву страви текстом, наприклад: омлет з сиром")
        return

    dish_name = clean_and_truncate(message.text)
    await message.answer("🔍 Аналізую страву...")
    profile = get_profile(message.from_user.id)

    try:
        recipe = await analyze_dish_by_name(dish_name, profile)
    except Exception as e:
        print(f"[ERROR] Dish analysis failed: {type(e).__name__}: {e}")
        await message.answer("⚠️ Не вдалось проаналізувати страву. Спробуй ще раз за хвилину.")
        return

    await _send_recipe_result(message, state, recipe)


@router.callback_query(F.data == "recipe_save")
async def handle_recipe_save(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    recipe = data.get("recipe")

    if recipe is None:
        await callback.answer("Рецепт застарів, спробуй підібрати новий", show_alert=True)
        return

    item = FoodItem(
        name=recipe["name"],
        weight_g=0,
        protein=recipe.get("protein", 0),
        fat=recipe.get("fat", 0),
        carbs=recipe.get("carbs", 0),
        kcal=recipe.get("kcal", 0),
    )
    analysis = MealAnalysis(
        items=[item],
        is_food=True,
        total_protein=item.protein,
        total_fat=item.fat,
        total_carbs=item.carbs,
        total_kcal=item.kcal,
    )
    save_meal(callback.from_user.id, analysis)
    await state.clear()

    await callback.answer("Додано в сьогоднішні прийоми їжі! ✅", show_alert=True)