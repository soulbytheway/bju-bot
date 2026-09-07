from aiogram.fsm.state import State, StatesGroup


class MealStates(StatesGroup):
    waiting_confirmation = State()
    waiting_correction_text = State()
    waiting_text_description = State()


class ProfileStates(StatesGroup):
    waiting_gender = State()
    waiting_birth_year = State()
    waiting_weight = State()
    waiting_height = State()
    waiting_activity = State()
    waiting_goal = State()
    waiting_allergies = State()


class RecipeStates(StatesGroup):
    waiting_dish_name = State()