from dataclasses import dataclass
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
    feed_kg_per_month: float
    notes: list[str]


# Mật độ tối ưu cho mô hình nuôi xen kẽ tôm sú – cua biển
_DENSITY = {
    FarmingModel.EXTENSIVE: {
        "shrimp": 5.0,   # PL/m²
        "crab":   0.3,   # con/m²
        "feed_ratio": 3, # kg thức ăn / kg tôm thu hoạch
    },
    FarmingModel.SEMI_INTENSIVE: {
        "shrimp": 12.0,
        "crab":   0.5,
        "feed_ratio": 2.5,
    },
}

# Ước tính sản lượng (kg/ha/vụ) để tính lượng thức ăn
_YIELD_KG_HA = {
    FarmingModel.EXTENSIVE: {"shrimp": 300, "crab": 150},
    FarmingModel.SEMI_INTENSIVE: {"shrimp": 800, "crab": 250},
}


def calculate_stocking(area_ha: float, model: FarmingModel = FarmingModel.EXTENSIVE) -> StockingResult:
    if area_ha <= 0:
        raise ValueError("Diện tích ao phải lớn hơn 0")

    d = _DENSITY[model]
    area_m2 = area_ha * 10_000

    shrimp_pl       = int(area_m2 * d["shrimp"])
    crab_juveniles  = int(area_m2 * d["crab"])

    # Ước tính thức ăn/tháng (6 tháng/vụ)
    yield_shrimp = _YIELD_KG_HA[model]["shrimp"] * area_ha
    feed_per_month = (yield_shrimp * d["feed_ratio"]) / 6

    notes = []
    if model == FarmingModel.EXTENSIVE:
        notes.append("Thả cua trước tôm 2 tuần để cua quen môi trường")
        notes.append("Không cho cua ăn riêng — cua ăn tảo, mùn bã hữu cơ tự nhiên")
    else:
        notes.append("Chia ao thành ô nhỏ bằng lưới mắt 1cm để hạn chế cua ăn tôm")
        notes.append("Theo dõi FCR hàng tuần, điều chỉnh lượng thức ăn")

    if area_ha > 2:
        notes.append(f"Ao lớn ({area_ha} ha): chia thành {int(area_ha)} khu thả riêng để dễ quản lý")

    return StockingResult(
        model=model.value,
        area_ha=area_ha,
        shrimp_pl=shrimp_pl,
        crab_juveniles=crab_juveniles,
        shrimp_density_per_m2=d["shrimp"],
        crab_density_per_m2=d["crab"],
        feed_kg_per_month=round(feed_per_month, 1),
        notes=notes,
    )
