from fastapi import APIRouter, HTTPException
from module_calculator.src.stocking_calculator import (
    calculate_stocking, FarmingModel,
)
from module_calculator.src.lime_calculator import calculate_lime
from module_calculator.src.probiotic_calculator import calculate_probiotic
from module_calculator.src.schedule_engine import generate_schedule, FarmPhase
from api.schemas.calculator import (
    StockingRequest,  StockingResponse,
    LimeRequest,      LimeResponse,
    ProbioticRequest, ProbioticResponse,
    ScheduleRequest,  ScheduleResponse,  ScheduleTaskResponse,
    RecommendRequest, RecommendResponse,
)

router = APIRouter(prefix="/calculator", tags=["Calculator"])


def _stocking_to_resp(r) -> StockingResponse:
    return StockingResponse(
        model=r.model, area_ha=r.area_ha,
        shrimp_pl=r.shrimp_pl, crab_juveniles=r.crab_juveniles,
        shrimp_density_m2=r.shrimp_density_per_m2,
        crab_density_m2=r.crab_density_per_m2,
        supplement_feed_kg_per_day=r.supplement_feed_kg_per_day,
        supplement_feed_kg_per_month=r.supplement_feed_kg_per_month,
        feed_type=getattr(r, "feed_type", None),
        notes=r.notes,
    )


def _lime_to_resp(r) -> LimeResponse:
    return LimeResponse(
        current_ph=r.current_ph, area_ha=r.area_ha,
        status=r.status, dolomite_kg=r.dolomite_kg,
        agricultural_lime_kg=r.agricultural_lime_kg,
        gypsum_kg=r.gypsum_kg, target_ph=r.target_ph,
        timing=r.timing, notes=r.notes, warning=r.warning,
    )


def _probiotic_to_resp(r) -> ProbioticResponse:
    return ProbioticResponse(
        area_ha=r.area_ha, bacillus_kg=r.bacillus_kg,
        em_liters=r.em_liters, apply_time=r.apply_time,
        frequency=r.frequency, next_dose_day=r.next_dose_day,
        notes=r.notes,
    )


@router.post("/stocking", response_model=StockingResponse)
def stocking(req: StockingRequest):
    try:
        return _stocking_to_resp(
            calculate_stocking(req.area_ha, FarmingModel(req.model))
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/lime", response_model=LimeResponse)
def lime(req: LimeRequest):
    try:
        return _lime_to_resp(
            calculate_lime(req.current_ph, req.area_ha,
                           pond_stage=req.pond_stage,
                           farming_model=req.farming_model)
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/probiotic", response_model=ProbioticResponse)
def probiotic(req: ProbioticRequest):
    try:
        return _probiotic_to_resp(
            calculate_probiotic(
                req.area_ha, req.temperature_c,
                req.days_since_last_dose, req.has_disease_sign,
                farming_model=req.farming_model,
                pond_stage=req.pond_stage,
            )
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/schedule", response_model=ScheduleResponse)
def schedule(req: ScheduleRequest):
    s = generate_schedule(
        req.start_date, FarmPhase(req.phase),
        req.duration_days, req.area_ha,
        farming_model=req.farming_model,
    )
    tasks = [
        ScheduleTaskResponse(
            date=t.date, task=t.task,
            category=t.category, priority=t.priority, note=t.note,
        )
        for t in s.tasks
    ]
    upcoming = [
        ScheduleTaskResponse(
            date=t.date, task=t.task,
            category=t.category, priority=t.priority, note=t.note,
        )
        for t in s.upcoming(7)
    ]
    return ScheduleResponse(
        farm_phase=s.farm_phase, start_date=s.start_date,
        tasks=tasks, upcoming_7d=upcoming,
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    """Tính toán toàn bộ trong 1 request — endpoint chính cho app."""
    try:
        stocking  = _stocking_to_resp(
            calculate_stocking(req.area_ha, FarmingModel(req.farming_model))
        )
        lime      = _lime_to_resp(
            calculate_lime(req.current_ph, req.area_ha,
                           pond_stage=req.pond_stage,
                           farming_model=req.farming_model)
        )
        probiotic = _probiotic_to_resp(
            calculate_probiotic(
                req.area_ha, req.temperature_c,
                req.days_since_probiotic, req.has_disease_sign,
                farming_model=req.farming_model,
                pond_stage=req.pond_stage,
            )
        )
        return RecommendResponse(stocking=stocking, lime=lime, probiotic=probiotic)
    except ValueError as e:
        raise HTTPException(400, str(e))
