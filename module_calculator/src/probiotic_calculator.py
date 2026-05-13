from dataclasses import dataclass


@dataclass
class ProbioticResult:
    area_ha: float
    bacillus_kg: float       # men vi sinh Bacillus dạng bột
    em_liters: float         # EM gốc pha loãng (1:100 trước khi tạt)
    apply_time: str
    frequency: str
    notes: list[str]
    next_dose_day: int       # số ngày đến lần tạt kế tiếp


# Liều cơ bản (kg Bacillus/ha/lần)
_BASE_BACILLUS = 1.0
_BASE_EM_LITERS = 2.0       # lít EM gốc/ha/lần (pha 1:100 thành 200 lít)

# Nhiệt độ nước ảnh hưởng đến tốc độ nhân vi khuẩn
_TEMP_FACTOR = {
    (0,  26): 1.5,   # lạnh → vi khuẩn chậm → tăng liều
    (26, 32): 1.0,   # lý tưởng
    (32, 50): 0.7,   # nóng → vi khuẩn tự nhân → giảm liều
}

# Ngày kể từ lần tạt cuối → hệ số cấp bách
def _urgency(days_since: int) -> tuple[float, int]:
    if days_since <= 3:
        return 0.5, 7          # vừa tạt → liều thấp, 7 ngày nữa
    if days_since <= 7:
        return 1.0, 5
    if days_since <= 14:
        return 1.3, 3
    return 1.8, 1              # quá lâu → liều cao, tạt lại ngay


# Hệ số theo mô hình canh tác
# extensive: ao rừng ngập mặn, thay nước triều → vi sinh bị pha loãng nhanh → liều thấp hơn
# semi_intensive: ao kín, ít thay nước → liều chuẩn
_FARMING_FACTOR = {"extensive": 0.4, "semi_intensive": 1.0}

# Hệ số theo giai đoạn ao
# preparation: cải tạo ao trước khi thả → tăng liều để xử lý đáy triệt để
# stocked: tôm đang nuôi → liều chuẩn
_STAGE_FACTOR = {"preparation": 1.5, "stocked": 1.0}


def calculate_probiotic(
    area_ha: float,
    temperature_c: float = 28.0,
    days_since_last_dose: int = 7,
    has_disease_sign: bool = False,
    farming_model: str = "extensive",
    pond_stage: str = "stocked",
) -> ProbioticResult:
    if area_ha <= 0:
        raise ValueError("Diện tích ao phải > 0")

    temp_factor    = next(
        (v for (lo, hi), v in _TEMP_FACTOR.items() if lo <= temperature_c < hi),
        1.0,
    )
    farming_factor = _FARMING_FACTOR.get(farming_model, 1.0)
    stage_factor   = _STAGE_FACTOR.get(pond_stage, 1.0)

    urgency_factor, next_dose_day = _urgency(days_since_last_dose)

    # Khi phát hiện dấu hiệu bệnh → tăng liều gấp đôi, tạt liên tiếp 3 ngày
    disease_factor = 2.0 if has_disease_sign else 1.0
    if has_disease_sign:
        next_dose_day = 1

    bacillus = _BASE_BACILLUS * temp_factor * urgency_factor * disease_factor * farming_factor * stage_factor * area_ha
    em = _BASE_EM_LITERS * temp_factor * urgency_factor * disease_factor * farming_factor * stage_factor * area_ha

    notes = [
        "Hoà tan men vi sinh vào nước ao (lấy nước ao, không dùng nước máy có Clo)",
        "Tắt quạt nước / sục khí 30 phút trước khi tạt để vi khuẩn định cư",
        "Bật lại sục khí sau 1 tiếng",
    ]
    if pond_stage == "preparation":
        notes.insert(0, "Giai đoạn cải tạo ao: tăng liều vi sinh 1.5x để xử lý đáy và phân hủy mùn bã")
    if farming_model == "extensive":
        notes.append("Mô hình quảng canh: ao thông triều — tạt vi sinh sau khi đóng cống ít nhất 12 giờ")
    if has_disease_sign:
        notes.insert(0, "CHẾ ĐỘ KHẨN CẤP: Tạt men vi sinh liên tiếp 3 ngày")
        notes.append("Kết hợp thay 20% nước ao nếu pH và độ mặn cho phép")
    if temperature_c > 32:
        notes.append(f"Nhiệt độ cao ({temperature_c}°C): giảm liều tự động để tránh tảo nở hoa")
    if temperature_c < 26:
        notes.append(f"Nhiệt độ thấp ({temperature_c}°C): tăng liều để bù hiệu quả vi khuẩn giảm")

    return ProbioticResult(
        area_ha=area_ha,
        bacillus_kg=round(bacillus, 2),
        em_liters=round(em, 1),
        apply_time="18:00 – 20:00 (sau khi mặt trời lặn)",
        frequency=f"Mỗi {next_dose_day} ngày/lần" if next_dose_day > 1 else "Hàng ngày (đang xử lý)",
        notes=notes,
        next_dose_day=next_dose_day,
    )
