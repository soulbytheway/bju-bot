import sqlite3
from datetime import date

from config import settings
from db.schemas import MealAnalysis, UserProfile


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            gender TEXT,
            birth_year INTEGER,
            weight REAL,
            height REAL,
            activity TEXT,
            goal TEXT,
            allergies TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            items_json TEXT NOT NULL,
            total_protein REAL,
            total_fat REAL,
            total_carbs REAL,
            total_kcal REAL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )
    conn.commit()
    conn.close()


def ensure_user_exists(user_id: int) -> None:
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_profile(user_id: int) -> UserProfile:
    conn = get_connection()
    row = conn.execute(
        "SELECT gender, birth_year, weight, height, activity, goal, allergies FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    if row is None:
        return UserProfile(user_id=user_id)

    return UserProfile(
        user_id=user_id,
        gender=row["gender"],
        birth_year=row["birth_year"],
        weight=row["weight"],
        height=row["height"],
        activity=row["activity"],
        goal=row["goal"],
        allergies=row["allergies"],
    )


def update_profile_field(user_id: int, field_name: str, value) -> None:
    allowed_fields = {"gender", "birth_year", "weight", "height", "activity", "goal", "allergies"}
    if field_name not in allowed_fields:
        raise ValueError(f"Недозволене поле профілю: {field_name}")

    conn = get_connection()
    conn.execute(f"UPDATE users SET {field_name} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()


def save_meal(user_id: int, analysis: MealAnalysis) -> None:
    import json

    items_json = json.dumps([item.__dict__ for item in analysis.items], ensure_ascii=False)

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO meals (user_id, items_json, total_protein, total_fat, total_carbs, total_kcal)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            items_json,
            analysis.total_protein,
            analysis.total_fat,
            analysis.total_carbs,
            analysis.total_kcal,
        ),
    )
    conn.commit()
    conn.close()


def get_today_totals(user_id: int) -> dict:
    today = date.today().isoformat()
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(total_protein), 0) AS protein,
            COALESCE(SUM(total_fat), 0) AS fat,
            COALESCE(SUM(total_carbs), 0) AS carbs,
            COALESCE(SUM(total_kcal), 0) AS kcal
        FROM meals
        WHERE user_id = ? AND date(timestamp) = date(?)
        """,
        (user_id, today),
    ).fetchone()
    conn.close()
    return dict(row)


def delete_user_data(user_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM meals WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_week_totals(user_id: int) -> list[dict]:
    """БЖУ/ккал по днях за останні 7 днів (тільки дні, де є записи)."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            date(timestamp) AS day,
            COALESCE(SUM(total_kcal), 0) AS kcal,
            COALESCE(SUM(total_protein), 0) AS protein,
            COALESCE(SUM(total_fat), 0) AS fat,
            COALESCE(SUM(total_carbs), 0) AS carbs
        FROM meals
        WHERE user_id = ? AND date(timestamp) >= date('now', '-6 days')
        GROUP BY date(timestamp)
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]