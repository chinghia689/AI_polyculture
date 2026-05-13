from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


class FarmPhase(str, Enum):
    PREPARATION  = "preparation"   # Chuẩn bị ao (trước thả giống)
    EARLY        = "early"         # Tháng 1–2
    MID          = "mid"           # Tháng 3–4
    LATE         = "late"          # Tháng 5–6 (gần thu hoạch)


@dataclass
class ScheduleTask:
    date: date
    task: str
    category: str     # water_test / trap_check / feed / treatment / harvest
    priority: str     # high / medium / low
    note: str = ""


@dataclass
class FarmSchedule:
    farm_phase: str
    start_date: date
    tasks: list[ScheduleTask] = field(default_factory=list)

    def upcoming(self, days: int = 7) -> list[ScheduleTask]:
        today = date.today()
        cutoff = today + timedelta(days=days)
        return [t for t in self.tasks if today <= t.date <= cutoff]


# Quy tắc lịch theo giai đoạn
_RULES = {
    FarmPhase.PREPARATION: {
        "water_test_days": 1,
        "trap_check_days": None,   # chưa thả
        "lime_days": 3,
        "probiotic_days": 7,
    },
    FarmPhase.EARLY: {
        "water_test_days": 2,
        "trap_check_days": 3,
        "feed_adjust_days": 5,
        "probiotic_days": 7,
    },
    FarmPhase.MID: {
        "water_test_days": 2,
        "trap_check_days": 2,
        "feed_adjust_days": 3,
        "probiotic_days": 5,
    },
    FarmPhase.LATE: {
        "water_test_days": 1,
        "trap_check_days": 1,
        "feed_adjust_days": 2,
        "probiotic_days": 5,
    },
}


def _add_recurring(
    tasks: list[ScheduleTask],
    start: date,
    days_total: int,
    interval: int,
    task_name: str,
    category: str,
    priority: str,
    note: str = "",
):
    current = start
    end = start + timedelta(days=days_total)
    while current <= end:
        tasks.append(ScheduleTask(
            date=current,
            task=task_name,
            category=category,
            priority=priority,
            note=note,
        ))
        current += timedelta(days=interval)


def generate_schedule(
    start_date: date,
    phase: FarmPhase,
    duration_days: int = 60,
    area_ha: float = 1.0,
) -> FarmSchedule:
    rules = _RULES[phase]
    tasks: list[ScheduleTask] = []

    # Đo nước
    _add_recurring(tasks, start_date, duration_days,
                   rules["water_test_days"],
                   "Đo pH, độ mặn, nhiệt độ, oxy hoà tan",
                   "water_test", "high",
                   "Đo lúc 6h sáng và 14h chiều")

    # Thăm lú (bẫy)
    if rules.get("trap_check_days"):
        _add_recurring(tasks, start_date, duration_days,
                       rules["trap_check_days"],
                       "Kiểm tra lú — ước lượng mật độ và tăng trưởng",
                       "trap_check", "medium",
                       "Đặt lú lúc 17h, thu lú lúc 5h sáng hôm sau")

    # Tạt vi sinh
    if rules.get("probiotic_days"):
        _add_recurring(tasks, start_date, duration_days,
                       rules["probiotic_days"],
                       "Tạt men vi sinh Bacillus",
                       "treatment", "medium",
                       "Tạt 18–20h, tắt quạt 30 phút trước")

    # Điều chỉnh thức ăn
    if rules.get("feed_adjust_days"):
        _add_recurring(tasks, start_date, duration_days,
                       rules["feed_adjust_days"],
                       "Kiểm tra sàng ăn — điều chỉnh lượng thức ăn",
                       "feed", "medium",
                       "Sàng ăn sau 2 tiếng, điều chỉnh ±10% nếu còn/hết")

    # Sự kiện cố định theo giai đoạn
    if phase == FarmPhase.PREPARATION:
        tasks.append(ScheduleTask(
            date=start_date + timedelta(days=3),
            task="Bón vôi lần 1 — diệt tạp, cải tạo đáy ao",
            category="treatment", priority="high",
            note=f"Liều theo máy tính vôi — khoảng {int(area_ha * 1000)} kg vôi nông nghiệp",
        ))
        tasks.append(ScheduleTask(
            date=start_date + timedelta(days=10),
            task="Gây màu nước — bón phân vi sinh NPK",
            category="treatment", priority="medium",
        ))
    elif phase == FarmPhase.LATE:
        tasks.append(ScheduleTask(
            date=start_date + timedelta(days=45),
            task="THU HOẠCH THỬ — cân mẫu 50 con, xác định size thương phẩm",
            category="harvest", priority="high",
        ))

    tasks.sort(key=lambda t: t.date)
    return FarmSchedule(farm_phase=phase.value, start_date=start_date, tasks=tasks)
