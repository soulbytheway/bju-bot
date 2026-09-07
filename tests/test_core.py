from datetime import date

from db.schemas import FoodItem, UserProfile, MealAnalysis
from services.nutrition import _calculate_totals, format_meal_response
from services.profile import calculate_bmr, calculate_daily_norm
from services.checks import is_valid_text_input, clean_and_truncate
from services.recipe import _build_allergy_note, format_recipe_message
from services.report import generate_weekly_chart, _last_7_days
import services.report as report_module


# ---------- services/nutrition.py ----------

def test_calculate_totals_sums_items_correctly():
    items = [
        FoodItem(name="куряче філе", weight_g=150, protein=31, fat=3.6, carbs=0, kcal=165),
        FoodItem(name="гречка", weight_g=100, protein=12.6, fat=3.3, carbs=62, kcal=313),
    ]
    result = _calculate_totals(items)

    assert result.total_kcal == 478
    assert result.total_protein == 43.6
    assert result.is_food is True


def test_calculate_totals_empty_list_returns_zeros():
    result = _calculate_totals([])
    assert result.total_kcal == 0
    assert result.total_protein == 0


def test_format_meal_response_includes_items_and_totals():
    items = [FoodItem(name="рис", weight_g=100, protein=2.7, fat=0.3, carbs=28, kcal=130)]
    analysis = _calculate_totals(items)
    text = format_meal_response(analysis)

    assert "рис" in text
    assert "130" in text


def test_format_meal_response_handles_no_food():
    analysis = MealAnalysis(items=[], is_food=False)
    text = format_meal_response(analysis)

    assert "не бачу" in text.lower()


# ---------- services/profile.py ----------

def test_calculate_bmr_male_formula():
    profile = UserProfile(
        user_id=1, gender="male", birth_year=2001, weight=80, height=180,
        activity="medium", goal="lose",
    )
    bmr = calculate_bmr(profile)
    expected = 10 * 80 + 6.25 * 180 - 5 * profile.age + 5
    assert bmr == expected


def test_calculate_bmr_female_lower_than_male_same_params():
    male = UserProfile(user_id=1, gender="male", birth_year=1996, weight=70, height=170, activity="medium", goal="maintain")
    female = UserProfile(user_id=2, gender="female", birth_year=1996, weight=70, height=170, activity="medium", goal="maintain")
    assert calculate_bmr(female) < calculate_bmr(male)


def test_calculate_daily_norm_deficit_for_weight_loss():
    profile_lose = UserProfile(user_id=1, gender="male", birth_year=2001, weight=80, height=180, activity="medium", goal="lose")
    profile_maintain = UserProfile(user_id=1, gender="male", birth_year=2001, weight=80, height=180, activity="medium", goal="maintain")

    norm_lose = calculate_daily_norm(profile_lose)
    norm_maintain = calculate_daily_norm(profile_maintain)

    assert norm_lose.kcal < norm_maintain.kcal


def test_calculate_daily_norm_raises_on_incomplete_profile():
    profile = UserProfile(user_id=1, gender="male")
    try:
        calculate_daily_norm(profile)
        assert False, "мало кинути ValueError на неповному профілі"
    except ValueError:
        pass


def test_profile_age_calculated_from_birth_year():
    profile = UserProfile(user_id=1, birth_year=date.today().year - 20)
    assert profile.age == 20


def test_profile_is_complete_false_when_missing_fields():
    profile = UserProfile(user_id=1, gender="male")
    assert profile.is_complete() is False


# ---------- services/checks.py ----------

def test_is_valid_text_input_rejects_none_and_empty():
    assert is_valid_text_input(None) is False
    assert is_valid_text_input("") is False
    assert is_valid_text_input("   ") is False


def test_is_valid_text_input_accepts_real_text():
    assert is_valid_text_input("куряче філе 150г") is True


def test_clean_and_truncate_strips_and_limits_length():
    long_text = "а" * 500
    result = clean_and_truncate(long_text, max_length=300)
    assert len(result) == 300
    assert clean_and_truncate("  привіт  ") == "привіт"


# ---------- services/recipe.py ----------

def test_build_allergy_note_empty_for_no_restrictions():
    assert _build_allergy_note(None) == ""
    assert _build_allergy_note("немає") == ""
    assert _build_allergy_note("нема") == ""


def test_build_allergy_note_includes_allergies_text():
    note = _build_allergy_note("горіхи, морепродукти")
    assert "горіхи" in note
    assert "морепродукти" in note


def test_format_recipe_message_includes_all_sections():
    recipe = {
        "name": "Омлет з сиром",
        "ingredients": ["2 яйця", "30г сиру"],
        "instructions": "Збий яйця, додай сир, готуй 5 хв.",
        "protein": 22, "fat": 18, "carbs": 3, "kcal": 270,
    }
    text = format_recipe_message(recipe)

    assert "Омлет з сиром" in text
    assert "2 яйця" in text
    assert "270" in text


# ---------- services/report.py ----------

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_last_7_days_returns_seven_dates_in_order():
    days = _last_7_days()
    assert len(days) == 7
    assert days == sorted(days)  # хронологічний порядок: найдавніший -> сьогодні
    assert days[-1] == date.today().isoformat()


def test_generate_weekly_chart_returns_valid_png_bytes(monkeypatch):
    days = _last_7_days()
    fake_rows = [
        {"day": days[0], "kcal": 2050},
        {"day": days[2], "kcal": 2430},
        {"day": days[5], "kcal": 2280},
    ]
    monkeypatch.setattr(report_module, "get_week_totals", lambda user_id: fake_rows)

    result = generate_weekly_chart(user_id=1, daily_kcal_norm=2200)

    assert isinstance(result, bytes)
    assert result[:8] == PNG_SIGNATURE


def test_generate_weekly_chart_fills_missing_days_with_zero(monkeypatch):
    # база повертає записи лише за 2 дні з 7 - решта мають підставитись нулями,
    # а не викликати помилку
    days = _last_7_days()
    fake_rows = [{"day": days[3], "kcal": 1800}]
    monkeypatch.setattr(report_module, "get_week_totals", lambda user_id: fake_rows)

    result = generate_weekly_chart(user_id=1, daily_kcal_norm=2000)

    assert result[:8] == PNG_SIGNATURE


def test_generate_weekly_chart_works_without_norm(monkeypatch):
    monkeypatch.setattr(report_module, "get_week_totals", lambda user_id: [])

    result = generate_weekly_chart(user_id=1, daily_kcal_norm=None)

    assert result[:8] == PNG_SIGNATURE


def test_generate_weekly_chart_empty_history_still_returns_png(monkeypatch):
    monkeypatch.setattr(report_module, "get_week_totals", lambda user_id: [])

    result = generate_weekly_chart(user_id=1)

    assert isinstance(result, bytes)
    assert len(result) > 0