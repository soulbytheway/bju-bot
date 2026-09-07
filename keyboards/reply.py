from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Додати їжу"), KeyboardButton(text="📊 Сьогодні")],
            [KeyboardButton(text="👤 Профіль"), KeyboardButton(text="📈 Звіти")],
            [KeyboardButton(text="🍽 Що приготувати"), KeyboardButton(text="⚙️ Налаштування")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )