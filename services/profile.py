from db.schemas import UserProfile, DailyNorm

ACTIVITY_MULTIPLIERS = {
    "low": 1.2,
    "medium": 1.55,
    "high": 1.9,
}

GOAL_MULTIPLIERS = {
    "lose": 0.8,
    "maintain": 1.0,
    "gain": 1.15,
}

def calculate_bmr(profile: UserProfile) -> float:
    base = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age
    if profile.gender == "male":
        return base + 5
    return base - 161


def calculate_daily_norm(profile: UserProfile) -> DailyNorm:
    if not profile.is_complete():
        raise ValueError("Профіль не заповнений повністю - неможливо розрахувати норму")

    bmr = calculate_bmr(profile)
    maintenance_kcal = bmr * ACTIVITY_MULTIPLIERS[profile.activity]
    target_kcal = maintenance_kcal * GOAL_MULTIPLIERS[profile.goal]

    protein_g = profile.weight * 1.8
    protein_kcal = protein_g * 4

    fat_kcal = target_kcal * 0.25
    fat_g = fat_kcal / 9

    carbs_kcal = target_kcal - protein_kcal - fat_kcal
    carbs_g = max(carbs_kcal / 4, 0)

    return DailyNorm(
        kcal=round(target_kcal),
        protein=round(protein_g, 1),
        fat=round(fat_g, 1),
        carbs=round(carbs_g, 1),
    )