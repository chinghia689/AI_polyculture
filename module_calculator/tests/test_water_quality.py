import pytest
from module_calculator.src.water_quality import assess_water_quality


class TestDO:
    def test_ok(self):
        r = assess_water_quality(do_mgl=5.5)
        assert r.overall_status == "ok"
        assert r.danger_count == 0

    def test_warning(self):
        r = assess_water_quality(do_mgl=3.0)
        assert r.overall_status == "warning"
        assert r.warning_count == 1

    def test_danger(self):
        r = assess_water_quality(do_mgl=1.5)
        assert r.overall_status == "danger"
        assert r.danger_count == 1
        assert r.priority_actions[0] is not None

    def test_boundary_ok_at_4(self):
        r = assess_water_quality(do_mgl=4.0)
        assert r.overall_status == "ok"


class TestAlkalinity:
    def test_danger_below_60(self):
        r = assess_water_quality(alkalinity=40)
        assert r.overall_status == "danger"

    def test_warning_60_80(self):
        r = assess_water_quality(alkalinity=70)
        assert r.overall_status == "warning"

    def test_ok_range(self):
        r = assess_water_quality(alkalinity=100)
        assert r.overall_status == "ok"

    def test_warning_above_150(self):
        r = assess_water_quality(alkalinity=200)
        assert r.overall_status == "warning"


class TestNH3:
    def test_safe(self):
        r = assess_water_quality(nh3_mgl=0.05)
        assert r.overall_status == "ok"

    def test_warning(self):
        r = assess_water_quality(nh3_mgl=0.2)
        assert r.overall_status == "warning"

    def test_danger(self):
        r = assess_water_quality(nh3_mgl=0.5)
        assert r.overall_status == "danger"
        assert "zeolite" in r.priority_actions[0]


class TestNO2:
    def test_safe(self):
        r = assess_water_quality(no2_mgl=0.3)
        assert r.overall_status == "ok"

    def test_warning(self):
        r = assess_water_quality(no2_mgl=0.7)
        assert r.overall_status == "warning"

    def test_danger(self):
        r = assess_water_quality(no2_mgl=2.0)
        assert r.overall_status == "danger"


class TestTransparency:
    def test_too_murky(self):
        r = assess_water_quality(transparency_cm=10)
        assert r.overall_status == "danger"

    def test_slightly_murky(self):
        r = assess_water_quality(transparency_cm=25)
        assert r.overall_status == "warning"

    def test_ideal(self):
        r = assess_water_quality(transparency_cm=35)
        assert r.overall_status == "ok"

    def test_too_clear(self):
        r = assess_water_quality(transparency_cm=60)
        assert r.overall_status == "warning"


class TestCombined:
    def test_no_params_returns_ok(self):
        r = assess_water_quality()
        assert r.overall_status == "ok"
        assert r.alerts == []

    def test_danger_dominates_warning(self):
        # DO=3 (warning) + NH3=0.5 (danger) → overall danger
        r = assess_water_quality(do_mgl=3.0, nh3_mgl=0.5)
        assert r.overall_status == "danger"
        assert r.danger_count == 1
        assert r.warning_count == 1

    def test_priority_actions_danger_first(self):
        r = assess_water_quality(do_mgl=3.0, nh3_mgl=0.5)
        # NH3 danger action should come before DO warning action
        assert "zeolite" in r.priority_actions[0]

    def test_multiple_ok(self):
        r = assess_water_quality(do_mgl=6.0, alkalinity=100, nh3_mgl=0.05)
        assert r.overall_status == "ok"
        assert r.danger_count == 0
        assert r.warning_count == 0


class TestGrowthNote:
    def test_stage_1(self):
        r = assess_water_quality(days_cultured=15)
        assert r.growth_note is not None
        assert "0–30" in r.growth_note

    def test_stage_4(self):
        r = assess_water_quality(days_cultured=100)
        assert r.growth_note is not None
        assert "thu hoạch" in r.growth_note.lower()

    def test_late_stage(self):
        r = assess_water_quality(days_cultured=150)
        assert r.growth_note is not None
        assert ">120" in r.growth_note

    def test_no_days_no_note(self):
        r = assess_water_quality(do_mgl=5.0)
        assert r.growth_note is None
