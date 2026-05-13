from dataclasses import dataclass


@dataclass
class LimeResult:
    current_ph: float
    area_ha: float
    status: str                  # ideal / acidic / alkaline / critical
    dolomite_kg: float           # vôi đá (CaMg(CO3)2) — nâng pH từ từ
    agricultural_lime_kg: float  # vôi nông nghiệp (CaCO3) — nâng pH nhanh
    gypsum_kg: float             # thạch cao (CaSO4) — hạ pH khi quá cao
    target_ph: str
    timing: str
    notes: list[str]
    warning: str | None


# Ao bán thâm canh / ao kín: liều chuẩn, xử lý triệt để
# (ph_min, ph_max, dolomite kg/ha, agri_lime kg/ha, gypsum kg/ha, status_key)
_LIME_TABLE_SEMI = [
    (0.0,  4.0, 3000, 2000, 0,   "critical_acid"),
    (4.0,  5.0, 2000, 1500, 0,   "acidic"),
    (5.0,  6.0, 1000,  750, 0,   "acidic"),
    (6.0,  6.5,  500,  300, 0,   "slightly_acidic"),
    (6.5,  7.0,  200,  100, 0,   "below_target"),   # tôm sú cần 7.5–8.0
    (7.0,  8.2,    0,    0, 0,   "ideal"),
    (8.2,  8.8,    0,    0, 200, "slightly_alkaline"),
    (8.8, 14.0,    0,    0, 500, "alkaline"),
]

# Vuông tôm quảng canh / ao rừng ngập mặn thông triều (ĐBSCL, U Minh, Cà Mau):
# - Chỉ dùng Dolomite (từ từ, không sốc hệ sinh thái rừng)
# - Không dùng vôi nông nghiệp CaCO₃ mạnh — giết phù du, vi sinh đáy tự nhiên
# - Triều tự cân bằng pH nên liều thấp hơn nhiều
# - Giai đoạn prep không nhân thêm — ao thông nước, liều cao bị triều cuốn đi lãng phí
_LIME_TABLE_EXTENSIVE = [
    (0.0,  4.0, 500,  0, 0,   "critical_acid"),   # phèn nặng — cần nhiều đợt nhỏ
    (4.0,  5.0, 300,  0, 0,   "acidic"),
    (5.0,  6.0, 150,  0, 0,   "acidic"),
    (6.0,  6.5,  80,  0, 0,   "slightly_acidic"),
    (6.5,  7.0,  50,  0, 0,   "below_target"),    # tôm sú cần 7.5–8.0
    (7.0,  8.2,   0,  0, 0,   "ideal"),
    (8.2,  8.8,   0,  0, 80,  "slightly_alkaline"),
    (8.8, 14.0,   0,  0, 200, "alkaline"),
]

_STATUS_LABEL = {
    "critical_acid":     "Nguy hiểm — pH quá thấp, tôm cua chết hàng loạt",
    "acidic":            "Chua — cần xử lý gấp",
    "slightly_acidic":   "Hơi chua — cần điều chỉnh",
    "below_target":      "Dưới mức lý tưởng — tôm sú cần pH 7.5–8.0",
    "ideal":             "Lý tưởng — không cần xử lý",
    "slightly_alkaline": "Hơi kiềm — theo dõi thêm",
    "alkaline":          "Kiềm cao — cần hạ pH",
}


def calculate_lime(
    current_ph: float,
    area_ha: float,
    pond_stage: str = "stocked",
    farming_model: str = "extensive",
) -> LimeResult:
    if not (0 < area_ha <= 1000):
        raise ValueError("Diện tích ao không hợp lệ")
    if not (0.0 <= current_ph <= 14.0):
        raise ValueError("pH phải trong khoảng 0–14")

    is_extensive = farming_model == "extensive"
    table = _LIME_TABLE_EXTENSIVE if is_extensive else _LIME_TABLE_SEMI

    row = next(
        (r for r in table if r[0] <= current_ph < r[1]),
        table[-1],
    )
    _, _, dolomite_base, agri_lime_base, gypsum_base, status_key = row

    # Ao bán thâm canh kín nước: cải tạo ao tăng 1.5× để xử lý đáy triệt để
    # Ao quảng canh thông triều: không tăng — liều cao bị triều cuốn, lãng phí
    prep = pond_stage == "preparation"
    stage_factor = 1.5 if (prep and not is_extensive) else 1.0

    dolomite  = dolomite_base  * stage_factor
    agri_lime = agri_lime_base * stage_factor
    gypsum    = gypsum_base

    notes = []
    warning = None

    if is_extensive:
        notes.append("Chỉ dùng Dolomite — không dùng vôi nông nghiệp mạnh cho ao rừng thông triều")
        if status_key != "ideal":
            notes.append("Chia làm 2–3 đợt tạt cách nhau 3 ngày, không tạt hết một lần")
            notes.append("Tạt gần cống cấp nước khi con triều lên để phân phối đều")
    elif prep:
        notes.insert(0, "Giai đoạn cải tạo ao: tăng liều vôi 1.5× để xử lý đáy, diệt mầm bệnh tồn dư")

    if status_key == "critical_acid":
        warning = "pH CỰC KỲ NGUY HIỂM — tạt vôi ngay lập tức, dừng cho ăn"
        notes.append("Rải vôi đều khắp mặt ao lúc 8–9 giờ sáng")
        notes.append("Đo lại pH sau 6 tiếng, lặp lại nếu chưa đạt 6.0")
        notes.append("Tuyệt đối KHÔNG thả giống khi pH < 6.0")
    elif status_key == "acidic":
        notes.append("Tạt vôi lúc sáng sớm (6–8h), tránh buổi chiều")
        notes.append("Đo lại pH sau 24 tiếng trước khi tạt thêm")
    elif status_key == "slightly_acidic":
        notes.append("Dolomite nâng pH từ từ, an toàn cho hệ sinh thái")
    elif status_key == "below_target":
        notes.append("pH còn thấp hơn mức lý tưởng — tạt Dolomite nhẹ, đo lại sau 2 ngày")
        notes.append("Không nâng pH quá 0.3 đơn vị/ngày tránh sốc tôm/cua")
    elif status_key == "ideal":
        if is_extensive:
            notes.append("Duy trì bằng cách theo dõi pH sau mỗi con triều")
        else:
            notes.append("Duy trì bằng cách tạt vôi phòng ngừa 50–100 kg/ha/tháng")
    elif "alkaline" in status_key:
        notes.append("Thay 20–30% nước ao trước khi tạt thạch cao")
        notes.append("Tăng sục khí để CO₂ hoà tan giúp hạ pH tự nhiên")
        if status_key == "alkaline":
            warning = "pH quá cao — tôm bị mềm vỏ, giảm ăn. Xử lý gấp"

    return LimeResult(
        current_ph=current_ph,
        area_ha=area_ha,
        status=_STATUS_LABEL[status_key],
        dolomite_kg=round(dolomite * area_ha, 1),
        agricultural_lime_kg=round(agri_lime * area_ha, 1),
        gypsum_kg=round(gypsum * area_ha, 1),
        target_ph="6.5 – 8.2",
        timing="6:00 – 9:00 sáng (tránh chiều)",
        notes=notes,
        warning=warning,
    )
