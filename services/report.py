import io
from datetime import date, timedelta
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
from db.database import get_week_totals


def _last_7_days() -> list[str]:
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]


def generate_weekly_chart(user_id: int, daily_kcal_norm: float | None = None) -> bytes:
    raw = {row["day"]: row for row in get_week_totals(user_id)}
    days = _last_7_days()

    kcal_values = [raw.get(d, {}).get("kcal", 0) for d in days]
    labels = [date.fromisoformat(d).strftime("%d.%m") for d in days]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, kcal_values, color="#4C9AFF", label="Спожито")

    if daily_kcal_norm:
        ax.axhline(y=daily_kcal_norm, color="#FF5630", linestyle="--", label=f"Норма (~{daily_kcal_norm:.0f} ккал)")

    ax.set_ylabel("Калорії, ккал")
    ax.set_title("Споживання калорій за останні 7 днів")
    ax.legend()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)  
    buf.seek(0)
    return buf.getvalue()