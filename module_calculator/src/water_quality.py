from dataclasses import dataclass, field


@dataclass
class WaterAlert:
    param: str       # key nội bộ
    label: str       # tên hiển thị
    value: float
    unit: str
    status: str      # "ok" | "warning" | "danger"
    message: str
    action: str | None


@dataclass
class WaterQualityResult:
    alerts: list[WaterAlert]
    danger_count: int
    warning_count: int
    priority_actions: list[str]  # các việc cần làm ngay, theo ưu tiên
    overall_status: str          # "ok" | "warning" | "danger"
    growth_note: str | None      # ghi chú về giai đoạn tăng trưởng


# (lo_inclusive, hi_exclusive, status, message, action)
_RULES: dict[str, dict] = {
    "do": {
        "label": "Oxy hòa tan (DO)",
        "unit": "mg/L",
        "ranges": [
            (0,   2,   "danger",  "Nguy hiểm — tôm có thể chết hàng loạt",
             "Bật toàn bộ quạt/sục khí NGAY, ngừng cho ăn, thay 20–30% nước sạch"),
            (2,   4,   "warning", "Tôm bị stress, giảm ăn, lớn chậm",
             "Tăng sục khí, thay 15% nước, tạm ngừng cho ăn 1 cữ"),
            (4,   10,  "ok",      "Đạt yêu cầu (lý tưởng 5–7 mg/L)", None),
        ],
    },
    "alkalinity": {
        "label": "Độ kiềm",
        "unit": "mg/L CaCO₃",
        "ranges": [
            (0,   60,  "danger",  "Kiềm quá thấp — pH dao động mạnh ban ngày, tôm khó lột xác",
             "Tạt Dolomite 150–200 kg/ha lúc 6–8h sáng, lặp lại sau 3 ngày"),
            (60,  80,  "warning", "Kiềm hơi thấp, cần bổ sung",
             "Tạt Dolomite 80–100 kg/ha, theo dõi sau 24h"),
            (80,  150, "ok",      "Lý tưởng", None),
            (150, 300, "warning", "Kiềm cao — theo dõi pH chiều tối",
             "Thay 10–15% nước, hạn chế bón phân gây tảo"),
        ],
    },
    "nh3": {
        "label": "NH₃ (Amoniac)",
        "unit": "mg/L",
        "ranges": [
            (0,    0.1,  "ok",      "An toàn", None),
            (0.1,  0.3,  "warning", "NH₃ tăng, tôm giảm ăn, dễ mắc bệnh",
             "Giảm 30% thức ăn, tạt Bacillus 1 kg/ha, tăng sục khí ban đêm"),
            (0.3,  9999, "danger",  "NH₃ nguy hiểm — tôm chết rải rác",
             "Ngừng cho ăn, thay 25–30% nước, tạt zeolite 20 kg/1.000 m³ + Bacillus khẩn cấp"),
        ],
    },
    "no2": {
        "label": "NO₂⁻ (Nitrite)",
        "unit": "mg/L",
        "ranges": [
            (0,   0.5,  "ok",      "An toàn", None),
            (0.5, 1.0,  "warning", "Nitrite tăng — tôm hấp thụ oxy kém hơn",
             "Thay 15–20% nước, thêm muối ăn 5 kg/1.000 m³, giảm thức ăn 20%"),
            (1.0, 9999, "danger",  "Nitrite nguy hiểm — tôm nổi đầu, đỏ mang",
             "Thay 30% nước ngay, thêm muối 10 kg/1.000 m³, ngừng cho ăn 1–2 ngày, tạt vi sinh"),
        ],
    },
    "transparency": {
        "label": "Độ trong (đĩa Secchi)",
        "unit": "cm",
        "ranges": [
            (0,   20,  "danger",  "Nước quá đục — tảo nở hoa hoặc phù sa cao",
             "Thay 20% nước, tạt zeolite 10–15 kg/1.000 m³, ngừng bón phân"),
            (20,  30,  "warning", "Nước hơi đục — tảo phát triển mạnh",
             "Theo dõi, nếu màu xanh đậm thay 10% nước"),
            (30,  45,  "ok",      "Lý tưởng — tảo phát triển cân bằng", None),
            (45,  999, "warning", "Nước trong quá — ít phiêu sinh vật, tôm thiếu thức ăn tự nhiên",
             "Gây màu: mật rỉ đường 2L + cám gạo 2 kg + vi sinh EM, ủ 24h rồi tạt/ha"),
        ],
    },
}

# Ghi chú tăng trưởng theo ngày nuôi (tôm sú quảng canh cải tiến)
_GROWTH_STAGES = [
    (0,   30,  "Giai đoạn 1 (0–30 ngày): tôm thích nghi — cho ăn nhẹ, theo dõi pH và DO sáng sớm hàng ngày"),
    (30,  60,  "Giai đoạn 2 (30–60 ngày): tăng trưởng nhanh — tôm ~80–120 con/kg, điều chỉnh thức ăn 3–5%/ngày"),
    (60,  90,  "Giai đoạn 3 (60–90 ngày): tôm ~40–80 con/kg, chú ý lột xác, kiểm tra kiềm và độ cứng"),
    (90,  120, "Giai đoạn 4 (90–120 ngày): chuẩn bị thu hoạch — tôm ~25–40 con/kg, giảm thức ăn, thu tỉa khi giá tốt"),
    (120, 999, "Giai đoạn cuối (>120 ngày): xem xét thu hoạch toàn bộ để tránh rủi ro bệnh và môi trường"),
]


def _check_param(key: str, value: float) -> WaterAlert:
    cfg = _RULES[key]
    for lo, hi, status, message, action in cfg["ranges"]:
        if lo <= value < hi:
            return WaterAlert(
                param=key, label=cfg["label"], value=value,
                unit=cfg["unit"], status=status, message=message, action=action,
            )
    # Ngoài bảng → fallback ok
    last = cfg["ranges"][-1]
    return WaterAlert(
        param=key, label=cfg["label"], value=value,
        unit=cfg["unit"], status="ok", message="Trong phạm vi bình thường", action=None,
    )


def assess_water_quality(
    do_mgl:           float | None = None,
    alkalinity:       float | None = None,
    nh3_mgl:          float | None = None,
    no2_mgl:          float | None = None,
    transparency_cm:  float | None = None,
    days_cultured:    int   | None = None,
) -> WaterQualityResult:
    alerts: list[WaterAlert] = []

    param_map = {
        "do":           do_mgl,
        "alkalinity":   alkalinity,
        "nh3":          nh3_mgl,
        "no2":          no2_mgl,
        "transparency": transparency_cm,
    }
    for key, val in param_map.items():
        if val is not None:
            alerts.append(_check_param(key, val))

    danger_count  = sum(1 for a in alerts if a.status == "danger")
    warning_count = sum(1 for a in alerts if a.status == "warning")

    # Priority actions: danger trước, warning sau
    priority_actions = [
        a.action for a in sorted(alerts, key=lambda x: 0 if x.status == "danger" else 1)
        if a.action
    ]

    if danger_count > 0:
        overall = "danger"
    elif warning_count > 0:
        overall = "warning"
    else:
        overall = "ok"

    growth_note = None
    if days_cultured is not None:
        for lo, hi, note in _GROWTH_STAGES:
            if lo <= days_cultured < hi:
                growth_note = note
                break

    return WaterQualityResult(
        alerts=alerts,
        danger_count=danger_count,
        warning_count=warning_count,
        priority_actions=priority_actions,
        overall_status=overall,
        growth_note=growth_note,
    )
