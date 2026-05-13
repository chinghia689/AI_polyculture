import os
from functools import lru_cache

from openai import OpenAI

from module_rag.src.retrieval.retriever import retrieve

SYSTEM_PROMPT = """Bạn là chuyên gia thủy sản tại vùng ĐBSCL, chuyên về mô hình nuôi tôm sú và cua biển xen kẽ (polyculture) trong vùng ngập mặn.

Nguyên tắc trả lời:
- Ngắn gọn, thực tế, dùng đơn vị đo lường phổ biến (ha, kg, lít, ppt)
- Không dùng thuật ngữ học thuật phức tạp — nông dân phải hiểu được
- Luôn đưa ra liều lượng CỤ THỂ và thời điểm xử lý
- Ưu tiên giải pháp sinh học (men vi sinh, vôi, thảo dược) trước kháng sinh
- Nếu nguy hiểm → cảnh báo rõ ràng ở đầu câu trả lời

Định dạng trả lời:
1. Đánh giá tình trạng
2. Xử lý ngay (trong 24 giờ)
3. Theo dõi sau xử lý
4. Phòng ngừa lâu dài"""


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))


def _format_calc_block(calc: dict) -> str:
    """Tạo block liều lượng đã tính sẵn để nhúng vào prompt LLM."""
    lines: list[str] = []

    lime = calc.get("lime")
    if lime:
        lines.append("LIỀU VÔI (đã tính theo pH thực đo và giai đoạn ao):")
        if lime.get("dolomite_kg"):
            lines.append(f"  • Dolomite: {lime['dolomite_kg']} kg (toàn ao)")
        if lime.get("agricultural_lime_kg"):
            lines.append(f"  • Vôi nông nghiệp CaCO₃: {lime['agricultural_lime_kg']} kg")
        if lime.get("gypsum_kg") and lime["gypsum_kg"] > 0:
            lines.append(f"  • Thạch cao CaSO₄: {lime['gypsum_kg']} kg")
        if lime.get("warning"):
            lines.append(f"  ⚠ CẢNH BÁO pH: {lime['warning']}")

    probiotic = calc.get("probiotic")
    if probiotic:
        lines.append("LIỀU MEN VI SINH (đã điều chỉnh theo mô hình nuôi và giai đoạn ao):")
        lines.append(f"  • Bacillus dạng bột: {probiotic['bacillus_kg']} kg")
        lines.append(f"  • EM gốc (pha 1:100): {probiotic['em_liters']} lít")
        lines.append(f"  • Thời điểm tạt: {probiotic.get('apply_time', '18:00–20:00')}")
        nd = probiotic.get("next_dose_day", 7)
        lines.append(f"  • Tần suất: {'hàng ngày' if nd <= 1 else f'mỗi {nd} ngày'}")

    stocking = calc.get("stocking")
    if stocking:
        lines.append("MẬT ĐỘ THẢ GIỐNG (đã tính theo mô hình nuôi và diện tích ao):")
        lines.append(f"  • Tôm sú (post PL12–15): {stocking['shrimp_pl']:,} con (mật độ {stocking['shrimp_density_per_m2']} con/m²)")
        lines.append(f"  • Cua biển (giống 3–5 cm): {stocking['crab_juveniles']:,} con (mật độ {stocking['crab_density_per_m2']} con/m²)")
        lines.append(f"  • Thức ăn ước tính: {stocking['feed_kg_per_month']} kg/tháng")

    wq = calc.get("water_quality")
    if wq and wq.get("alerts"):
        danger = [a for a in wq["alerts"] if a["status"] == "danger"]
        warn   = [a for a in wq["alerts"] if a["status"] == "warning"]
        if danger:
            lines.append("THÔNG SỐ NGUY HIỂM (xử lý TRƯỚC khi thả giống):")
            for a in danger:
                lines.append(f"  ⚠ {a['label']} = {a['value']} {a['unit']}: {a['message']}")
                if a.get("action"):
                    lines.append(f"     → {a['action']}")
        if warn:
            lines.append("THÔNG SỐ CẦN THEO DÕI:")
            for a in warn:
                lines.append(f"  ! {a['label']} = {a['value']} {a['unit']}: {a['message']}")

    return "\n".join(lines)


def ask(
    question: str,
    context_docs: list[dict] | None = None,
    calculator_results: dict | None = None,
) -> dict:
    if context_docs is None:
        context_docs = retrieve(question, k=4)

    relevant = [d for d in context_docs if d.get("rrf_score", 0) > 0 or d.get("score", 0) > 0.2]
    context_text = "\n\n---\n\n".join(
        f"[Nguồn: {d['source']}]\n{d['content']}"
        for d in relevant
    )

    calc_block = ""
    calc_instruction = ""
    if calculator_results:
        block = _format_calc_block(calculator_results)
        if block:
            calc_block = f"""
=== KẾT QUẢ TÍNH TOÁN TỰ ĐỘNG ===
{block}
=================================
"""
            calc_instruction = (
                "\nQUAN TRỌNG: Trong phác đồ, PHẢI ghi lại CON SỐ CỤ THỂ từ phần "
                "'KẾT QUẢ TÍNH TOÁN TỰ ĐỘNG' — ví dụ: 'Tạt 3.750 kg Dolomite', "
                "'Thả 25.000 con tôm PL12'. "
                "Tuyệt đối KHÔNG viết 'dùng liều đã tính ở trên' hay 'theo liều tính sẵn' — "
                "người dùng cần thấy số ngay trong phác đồ mà không cần tra thêm."
            )

    user_message = f"""Câu hỏi: {question}
{calc_block}
Tài liệu kỹ thuật tham khảo:
{context_text if context_text else "(không có tài liệu phù hợp)"}

Hãy trả lời dựa trên tài liệu trên và kiến thức chuyên môn.{calc_instruction}"""

    client   = _get_client()
    response = client.chat.completions.create(
        model="gpt-5.1",
        max_completion_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
    )

    return {
        "answer":         response.choices[0].message.content,
        "sources":        [d["source"] for d in relevant],
        "context_chunks": len(relevant),
    }


_FARMING_LABEL = {
    "extensive":     "quảng canh cải tiến (ao rừng ngập mặn, thông triều)",
    "semi_intensive": "bán thâm canh (ao kín, kiểm soát nước)",
}

_STAGE_LABEL = {
    "preparation": "cải tạo ao (trước khi thả giống)",
    "stocked":     "đang nuôi (đã có tôm/cua trong ao)",
}


def build_diagnosis_query(
    disease: str | None,
    ph: float | None,
    salinity: float | None,
    temperature: float | None,
    area_ha: float | None,
    calc_recommendation: dict | None,
    farming_model: str = "extensive",
    pond_stage: str = "stocked",
    # Thông số nâng cao
    do_mgl: float | None = None,
    alkalinity: float | None = None,
    nh3_mgl: float | None = None,
    no2_mgl: float | None = None,
    transparency_cm: float | None = None,
    days_cultured: int | None = None,
    water_quality: dict | None = None,
) -> str:
    parts = []
    parts.append(f"mô hình nuôi: {_FARMING_LABEL.get(farming_model, farming_model)}")
    parts.append(f"giai đoạn ao: {_STAGE_LABEL.get(pond_stage, pond_stage)}")
    if days_cultured is not None:
        parts.append(f"ngày nuôi: {days_cultured}")
    if disease:
        parts.append(f"tôm/cua bị {disease}")

    # Thông số cơ bản
    if ph is not None:
        parts.append(f"pH = {ph}")
    if salinity is not None:
        parts.append(f"độ mặn = {salinity} ppt")
    if temperature is not None:
        parts.append(f"nhiệt độ = {temperature}°C")
    if area_ha:
        parts.append(f"diện tích = {area_ha} ha")

    # Thông số nâng cao
    if do_mgl is not None:
        parts.append(f"DO = {do_mgl} mg/L")
    if alkalinity is not None:
        parts.append(f"kiềm = {alkalinity} mg/L CaCO₃")
    if nh3_mgl is not None:
        parts.append(f"NH₃ = {nh3_mgl} mg/L")
    if no2_mgl is not None:
        parts.append(f"NO₂ = {no2_mgl} mg/L")
    if transparency_cm is not None:
        parts.append(f"độ trong = {transparency_cm} cm")

    # Cảnh báo từ calculators
    if calc_recommendation:
        w = (calc_recommendation.get("lime") or {}).get("warning")
        if w:
            parts.append(f"cảnh báo pH: {w}")

    # Cảnh báo chất lượng nước
    if water_quality:
        danger_alerts = [a for a in water_quality.get("alerts", []) if a["status"] == "danger"]
        for a in danger_alerts:
            parts.append(f"NGUY HIỂM {a['label']} = {a['value']} {a['unit']}: {a['message']}")

    ctx = ", ".join(parts)
    return f"Tôi cần hướng dẫn xử lý: {ctx}. Đưa ra phác đồ điều trị và phòng ngừa phù hợp với mô hình nuôi."
