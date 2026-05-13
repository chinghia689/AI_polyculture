import pytest
from datetime import date

from module_calculator.src.stocking_calculator import calculate_stocking, FarmingModel
from module_calculator.src.lime_calculator import calculate_lime
from module_calculator.src.probiotic_calculator import calculate_probiotic
from module_calculator.src.schedule_engine import generate_schedule, FarmPhase


# ── Stocking ──────────────────────────────────────────────────────────────────
class TestStocking:
    def test_extensive_1ha(self):
        r = calculate_stocking(1.0, FarmingModel.EXTENSIVE)
        assert r.shrimp_pl == 50_000        # 5 PL/m² × 10,000 m²
        assert r.crab_juveniles == 3_000    # 0.3 con/m²
        assert r.supplement_feed_kg_per_month > 0

    def test_semi_intensive_2ha(self):
        r = calculate_stocking(2.0, FarmingModel.SEMI_INTENSIVE)
        assert r.shrimp_pl == 240_000       # 12 PL/m² × 20,000 m²
        assert r.crab_juveniles == 10_000
        assert len(r.notes) > 0

    def test_invalid_area(self):
        with pytest.raises(ValueError):
            calculate_stocking(-1)

    def test_large_farm_note(self):
        r = calculate_stocking(3.0)
        assert any("chia" in n for n in r.notes)


# ── Lime ──────────────────────────────────────────────────────────────────────
class TestLime:
    def test_ideal_ph(self):
        r = calculate_lime(7.5, 1.0)
        assert r.dolomite_kg == 0
        assert r.agricultural_lime_kg == 0
        assert r.gypsum_kg == 0
        assert r.warning is None

    def test_critical_acid(self):
        # Bán thâm canh — liều đầy đủ
        r = calculate_lime(3.5, 1.0, farming_model="semi_intensive")
        assert r.dolomite_kg == 3000
        assert r.warning is not None
        assert "NGUY HIỂM" in r.warning or "CỰC KỲ" in r.warning

    def test_critical_acid_extensive(self):
        # Quảng canh ao rừng — liều thấp hơn nhiều
        r = calculate_lime(3.5, 1.0, farming_model="extensive")
        assert r.dolomite_kg == 500
        assert r.agricultural_lime_kg == 0   # không dùng vôi mạnh cho ao rừng
        assert r.warning is not None

    def test_alkaline(self):
        r = calculate_lime(9.0, 2.0, farming_model="semi_intensive")
        assert r.gypsum_kg == 1000           # 500 kg/ha × 2 ha
        assert r.dolomite_kg == 0

    def test_slightly_acid_1ha(self):
        # Bán thâm canh — liều đầy đủ
        r = calculate_lime(6.2, 1.0, farming_model="semi_intensive")
        assert r.dolomite_kg == 500
        assert r.agricultural_lime_kg == 300

    def test_slightly_acid_extensive(self):
        # Quảng canh — liều thấp, chỉ dolomite
        r = calculate_lime(6.2, 1.0, farming_model="extensive")
        assert r.dolomite_kg == 80
        assert r.agricultural_lime_kg == 0

    def test_area_scaling(self):
        r1 = calculate_lime(5.0, 1.0)
        r2 = calculate_lime(5.0, 3.0)
        assert r2.dolomite_kg == r1.dolomite_kg * 3

    def test_invalid_ph(self):
        with pytest.raises(ValueError):
            calculate_lime(15.0, 1.0)


# ── Probiotic ─────────────────────────────────────────────────────────────────
class TestProbiotic:
    def test_normal_dose(self):
        r = calculate_probiotic(1.0, temperature_c=28, days_since_last_dose=7)
        assert r.bacillus_kg > 0
        assert r.em_liters > 0
        assert r.next_dose_day == 5

    def test_disease_mode(self):
        r = calculate_probiotic(1.0, has_disease_sign=True)
        normal = calculate_probiotic(1.0, has_disease_sign=False)
        assert r.bacillus_kg > normal.bacillus_kg
        assert r.next_dose_day == 1

    def test_high_temp_reduces_dose(self):
        cold = calculate_probiotic(1.0, temperature_c=24)
        hot  = calculate_probiotic(1.0, temperature_c=34)
        assert cold.bacillus_kg > hot.bacillus_kg

    def test_area_scaling(self):
        r1 = calculate_probiotic(1.0)
        r2 = calculate_probiotic(2.0)
        assert abs(r2.bacillus_kg - r1.bacillus_kg * 2) < 0.01


# ── Schedule ──────────────────────────────────────────────────────────────────
class TestSchedule:
    def test_generates_tasks(self):
        s = generate_schedule(date.today(), FarmPhase.EARLY)
        assert len(s.tasks) > 0

    def test_preparation_has_lime_task(self):
        s = generate_schedule(date.today(), FarmPhase.PREPARATION)
        categories = [t.category for t in s.tasks]
        assert "treatment" in categories

    def test_late_phase_has_harvest_task(self):
        s = generate_schedule(date.today(), FarmPhase.LATE, duration_days=60)
        tasks_text = " ".join(t.task for t in s.tasks)
        assert "THU HOẠCH" in tasks_text

    def test_tasks_sorted_by_date(self):
        s = generate_schedule(date.today(), FarmPhase.MID)
        dates = [t.date for t in s.tasks]
        assert dates == sorted(dates)

    def test_upcoming_filter(self):
        s = generate_schedule(date.today(), FarmPhase.EARLY)
        upcoming = s.upcoming(days=7)
        assert all(t.date >= date.today() for t in upcoming)
