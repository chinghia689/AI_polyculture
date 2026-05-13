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


# Quảng canh cải tiến / ao rừng ngập mặn:
# - Mật độ thấp, triều tự điều tiết → ít can thiệp hơn
# - Probiotic mỗi 7 ngày (tidal cuốn bớt, dùng dày không hiệu quả)
# - Trap check ít hơn (mật độ thấp, tôm/cua trú trong rừng)
# - Không dùng phân NPK để gây màu
_RULES_EXTENSIVE = {
    FarmPhase.PREPARATION: {
        "water_test_days":  2,
        "trap_check_days":  None,
        "lime_days":        5,
        "probiotic_days":   7,
    },
    FarmPhase.EARLY: {
        "water_test_days":  2,
        "trap_check_days":  7,
        "feed_adjust_days": 7,
        "probiotic_days":   7,
    },
    FarmPhase.MID: {
        "water_test_days":  2,
        "trap_check_days":  5,
        "feed_adjust_days": 5,
        "probiotic_days":   7,
    },
    FarmPhase.LATE: {
        "water_test_days":  2,
        "trap_check_days":  3,
        "feed_adjust_days": 3,
        "probiotic_days":   7,
    },
}

# Bán thâm canh / ao kín:
# - Mật độ cao, không có triều → kiểm soát chặt hơn
# - Probiotic mỗi 5 ngày
# - Điều chỉnh thức ăn thường xuyên hơn
_RULES_SEMI = {
    FarmPhase.PREPARATION: {
        "water_test_days":  1,
        "trap_check_days":  None,
        "lime_days":        3,
        "probiotic_days":   7,
    },
    FarmPhase.EARLY: {
        "water_test_days":  2,
        "trap_check_days":  3,
        "feed_adjust_days": 5,
        "probiotic_days":   7,
    },
    FarmPhase.MID: {
        "water_test_days":  2,
        "trap_check_days":  2,
        "feed_adjust_days": 3,
        "probiotic_days":   5,
    },
    FarmPhase.LATE: {
        "water_test_days":  1,
        "trap_check_days":  1,
        "feed_adjust_days": 2,
        "probiotic_days":   5,
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
            date=current, task=task_name,
            category=category, priority=priority, note=note,
        ))
        current += timedelta(days=interval)


def generate_schedule(
    start_date: date,
    phase: FarmPhase,
    duration_days: int = 60,
    area_ha: float = 1.0,
    farming_model: str = "extensive",
) -> FarmSchedule:
    is_extensive = farming_model == "extensive"
    rules = (_RULES_EXTENSIVE if is_extensive else _RULES_SEMI)[phase]
    tasks: list[ScheduleTask] = []

    # Đo nước
    _add_recurring(tasks, start_date, duration_days,
                   rules["water_test_days"],
                   "Đo pH, độ mặn, nhiệt độ, DO" + (" (sau mỗi con triều)" if is_extensive else ""),
                   "water_test", "high",
                   "Đo lúc 6h sáng và 14h chiều")

    # Thăm lú / bẫy
    if rules.get("trap_check_days"):
        note = ("Đặt lú ven rừng lúc 17h, thu lú lúc 5h sáng hôm sau"
                if is_extensive else
                "Đặt lú lúc 17h, thu lú lúc 5h sáng hôm sau")
        _add_recurring(tasks, start_date, duration_days,
                       rules["trap_check_days"],
                       "Kiểm tra lú — ước lượng mật độ và tăng trưởng",
                       "trap_check", "medium", note)

    # Tạt vi sinh
    if rules.get("probiotic_days"):
        probiotic_note = ("Tạt 18–20h, đóng cống trước khi tạt ít nhất 12h"
                          if is_extensive else
                          "Tạt 18–20h, tắt quạt 30 phút trước")
        _add_recurring(tasks, start_date, duration_days,
                       rules["probiotic_days"],
                       "Tạt men vi sinh Bacillus + EM",
                       "treatment", "medium", probiotic_note)

    # Điều chỉnh thức ăn
    if rules.get("feed_adjust_days"):
        _add_recurring(tasks, start_date, duration_days,
                       rules["feed_adjust_days"],
                       "Kiểm tra sàng ăn — điều chỉnh lượng thức ăn",
                       "feed", "medium",
                       "Sàng ăn sau 2 tiếng, điều chỉnh ±10% nếu còn/hết")

    # Bón vôi định kỳ giai đoạn cải tạo
    if rules.get("lime_days"):
        lime_note = (f"Dolomite ~{int(area_ha * 80)} kg, tạt gần cống khi triều lên"
                     if is_extensive else
                     f"Vôi nông nghiệp ~{int(area_ha * 1000)} kg, rải đều mặt ao")
        _add_recurring(tasks, start_date, duration_days,
                       rules["lime_days"],
                       "Bón vôi — cải tạo đáy, nâng pH",
                       "treatment", "high", lime_note)

    # Sự kiện cố định theo giai đoạn + mô hình
    if phase == FarmPhase.PREPARATION:
        if is_extensive:
            tasks.append(ScheduleTask(
                date=start_date + timedelta(days=7),
                task="Gây màu nước sinh học",
                category="treatment", priority="medium",
                note="Ủ mật rỉ đường 2L + cám gạo 2kg + vi sinh EM/ha, tạt sau 24h lên men",
            ))
            tasks.append(ScheduleTask(
                date=start_date + timedelta(days=14),
                task="Diệt tạp bằng Saponin",
                category="treatment", priority="high",
                note=f"Saponin 10 kg/1.000 m³ nước, tạt lúc 8–10h nắng, giữ nước 3–5 ngày",
            ))
        else:
            tasks.append(ScheduleTask(
                date=start_date + timedelta(days=3),
                task="Bón vôi lần 1 — diệt tạp, cải tạo đáy ao",
                category="treatment", priority="high",
                note=f"~{int(area_ha * 1000)} kg vôi nông nghiệp, rải đều lúc 8–9h sáng",
            ))
            tasks.append(ScheduleTask(
                date=start_date + timedelta(days=10),
                task="Gây màu nước — bón phân NPK",
                category="treatment", priority="medium",
                note="NPK 16-16-8: 1–2 kg/1.000 m³, kết hợp vi sinh",
            ))

    elif phase == FarmPhase.LATE:
        harvest_day = 90 if is_extensive else 45
        tasks.append(ScheduleTask(
            date=start_date + timedelta(days=harvest_day),
            task="THU HOẠCH THỬ — cân mẫu 50 con, xác định size thương phẩm",
            category="harvest", priority="high",
            note=("Tôm sú quảng canh thu hoạch khi đạt 25–40 con/kg (~90–120 ngày)"
                  if is_extensive else
                  "Tôm đạt 20–30 con/kg, kiểm tra FCR trước khi quyết định thu"),
        ))

    tasks.sort(key=lambda t: t.date)
    return FarmSchedule(farm_phase=phase.value, start_date=start_date, tasks=tasks)
