from dataclasses import dataclass, field
from enum import Enum


class FarmingModel(str, Enum):
    EXTENSIVE = "extensive"           # Quảng canh cải tiến
    SEMI_INTENSIVE = "semi_intensive" # Bán thâm canh


@dataclass
class StockingResult:
    model: str
    area_ha: float
    shrimp_pl: int
    crab_juveniles: int
    shrimp_density_per_m2: float
    crab_density_per_m2: float
    # Thức ăn bổ sung thực tế mua về (không tính thức ăn tự nhiên trong ao)
    supplement_feed_kg_per_day: float
    supplement_feed_kg_per_month: float
    feed_type: str          # loại thức ăn và cỡ viên
    notes: list[str] = field(default_factory=list)


# Mật độ tối ưu (con/m²)
_DENSITY = {
    FarmingModel.EXTENSIVE: {
        "shrimp": 5.0,
        "crab":   0.3,
    },
    FarmingModel.SEMI_INTENSIVE: {
        "shrimp": 12.0,
        "crab":   0.5,
    },
}

# Lượng thức ăn BỔ SUNG thực tế (kg/ha/ngày)
# Quảng canh: tôm/cua ăn chủ yếu thức ăn tự nhiên (phiêu sinh, sinh vật đáy,
#   mùn hữu cơ rừng ngập mặn), chỉ bổ sung 1–2 kg/ha/ngày.
# Bán thâm canh: phụ thuộc hoàn toàn thức ăn công nghiệp, 3–5 kg/ha/ngày.
_SUPPLEMENT_KG_HA_DAY = {
    FarmingModel.EXTENSIVE:     1.5,   # trung bình 1–2 kg/ha/ngày
    FarmingModel.SEMI_INTENSIVE: 4.0,  # trung bình 3–5 kg/ha/ngày
}

_FEED_TYPE = {
    FarmingModel.EXTENSIVE: (
        "Thức ăn viên tôm công nghiệp protein 30–35%; "
        "cỡ số 1–2 (giai đoạn đầu 1–45 ngày), số 3–4 (sau 45 ngày). "
        "Cua biển không cho ăn riêng — ăn hoàn toàn tự nhiên."
    ),
    FarmingModel.SEMI_INTENSIVE: (
        "Thức ăn viên tôm công nghiệp protein 35–42%; "
        "cỡ số 1–2 (tháng 1), số 3 (tháng 2), số 4 (tháng 3+). "
        "Kiểm tra sàng ăn sau 2 giờ, điều chỉnh tránh dư thừa."
    ),
}


def calculate_stocking(area_ha: float, model: FarmingModel = FarmingModel.EXTENSIVE) -> StockingResult:
    if area_ha <= 0:
        raise ValueError("Diện tích ao phải lớn hơn 0")

    d        = _DENSITY[model]
    area_m2  = area_ha * 10_000

    shrimp_pl      = int(area_m2 * d["shrimp"])
    crab_juveniles = int(area_m2 * d["crab"])

    kg_per_ha_day   = _SUPPLEMENT_KG_HA_DAY[model]
    feed_per_day    = round(kg_per_ha_day * area_ha, 1)
    feed_per_month  = round(feed_per_day * 30, 0)

    notes = []
    if model == FarmingModel.EXTENSIVE:
        notes.append("Thả cua trước tôm 2 tuần để cua quen môi trường")
        notes.append("Không cho cua ăn riêng — cua ăn tảo, mùn bã hữu cơ, sinh vật đáy tự nhiên")
        notes.append("Khi NO₂ hoặc NH₃ tăng: giảm 30% thức ăn ngay, không chờ")
        notes.append("Cho ăn 2 cữ/ngày (6h sáng, 17h chiều), rải đều tránh tập trung một điểm")
    else:
        notes.append("Chia ao thành ô nhỏ bằng lưới mắt 1 cm để hạn chế cua ăn tôm")
        notes.append("Theo dõi FCR hàng tuần, điều chỉnh lượng thức ăn theo tăng trưởng")
        notes.append("Dùng sàng ăn: kiểm tra sau 2h, nếu còn dư >20% → giảm khẩu phần")

    if area_ha > 2:
        notes.append(f"Ao lớn ({area_ha} ha): chia thành {int(area_ha)} khu thả riêng để dễ quản lý")

    return StockingResult(
        model=model.value,
        area_ha=area_ha,
        shrimp_pl=shrimp_pl,
        crab_juveniles=crab_juveniles,
        shrimp_density_per_m2=d["shrimp"],
        crab_density_per_m2=d["crab"],
        supplement_feed_kg_per_day=feed_per_day,
        supplement_feed_kg_per_month=feed_per_month,
        feed_type=_FEED_TYPE[model],
        notes=notes,
    )
