from dataclasses import dataclass, field
from datetime import date


@dataclass
class FoodItem:
    name: str
    weight_g: float
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0
    kcal: float = 0.0


@dataclass
class MealAnalysis:
    items: list[FoodItem] = field(default_factory=list)
    is_food: bool = True
    total_protein: float = 0.0
    total_fat: float = 0.0
    total_carbs: float = 0.0
    total_kcal: float = 0.0


@dataclass
class UserProfile:
    user_id: int
    gender: str | None = None
    birth_year: int | None = None
    weight: float | None = None
    height: float | None = None
    activity: str | None = None
    goal: str | None = None
    allergies: str | None = None

    def is_complete(self) -> bool:
        return all(
            v is not None
            for v in [self.gender, self.birth_year, self.weight, self.height, self.activity, self.goal]
        )

    @property
    def age(self) -> int | None:
        if self.birth_year is None:
            return None
        return date.today().year - self.birth_year


@dataclass
class DailyNorm:
    kcal: float
    protein: float
    fat: float
    carbs: float