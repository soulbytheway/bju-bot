from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def meal_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Все вірно", callback_data="meal_confirm"),
                InlineKeyboardButton(text="✏️ Виправити", callback_data="meal_correct"),
            ],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="meal_cancel")],
        ]
    )


def add_food_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⌨️ Описати текстом", callback_data="meal_text_input")],
        ]
    )


def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Чоловіча", callback_data="gender_male"),
                InlineKeyboardButton(text="Жіноча", callback_data="gender_female"),
            ]
        ]
    )


def activity_keyboard(show_back: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Низька (сидяча робота)", callback_data="activity_low")],
        [InlineKeyboardButton(text="Середня (тренування 3-5 р/тиждень)", callback_data="activity_medium")],
        [InlineKeyboardButton(text="Висока (щоденні тренування)", callback_data="activity_high")],
    ]
    if show_back:
        keyboard.append([InlineKeyboardButton(text="◀ Назад", callback_data="profile_edit_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def goal_keyboard(show_back: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Схуднення", callback_data="goal_lose")],
        [InlineKeyboardButton(text="Підтримка ваги", callback_data="goal_maintain")],
        [InlineKeyboardButton(text="Набір маси", callback_data="goal_gain")],
    ]
    if show_back:
        keyboard.append([InlineKeyboardButton(text="◀ Назад", callback_data="profile_edit_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Видалити мої дані", callback_data="settings_delete_data")],
        ]
    )


def confirm_delete_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Так, видалити все", callback_data="settings_delete_confirm"),
                InlineKeyboardButton(text="❌ Скасувати", callback_data="settings_delete_cancel"),
            ]
        ]
    )


def recipe_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Запропонуй під мій ліміт", callback_data="recipe_suggest")],
            [InlineKeyboardButton(text="✏️ Ввести назву страви", callback_data="recipe_by_name")],
        ]
    )


def meal_category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌅 Сніданок", callback_data="category_breakfast")],
            [InlineKeyboardButton(text="☀️ Обід", callback_data="category_lunch")],
            [InlineKeyboardButton(text="🌙 Вечеря", callback_data="category_dinner")],
            [InlineKeyboardButton(text="🍎 Перекус", callback_data="category_snack")],
            [InlineKeyboardButton(text="◀ Назад", callback_data="recipe_menu_back")],
        ]
    )


def recipe_result_keyboard(video_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Відео-рецепт", url=video_url)],
            [InlineKeyboardButton(text="✅ Додати цей прийом їжі", callback_data="recipe_save")],
            [InlineKeyboardButton(text="◀ Назад до вибору рецепту", callback_data="recipe_menu_back")],
        ]
    )


def profile_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚖️ Вага", callback_data="edit_weight")],
            [InlineKeyboardButton(text="📏 Зріст", callback_data="edit_height")],
            [InlineKeyboardButton(text="🏃 Активність", callback_data="edit_activity")],
            [InlineKeyboardButton(text="🎯 Ціль", callback_data="edit_goal")],
            [InlineKeyboardButton(text="🎂 Рік народження", callback_data="edit_birth_year")],
            [InlineKeyboardButton(text="🚫 Алергії", callback_data="edit_allergies")],
        ]
    )


def profile_view_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редагувати", callback_data="profile_edit_menu")],
        ]
    )