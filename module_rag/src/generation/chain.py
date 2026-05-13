import os
from functools import lru_cache

import anthropic

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
def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def ask(question: str, context_docs: list[dict] | None = None) -> dict:
    if context_docs is None:
        context_docs = retrieve(question, k=4)

    relevant = [d for d in context_docs if d["score"] > 0.2]
    context_text = "\n\n---\n\n".join(
        f"[Nguồn: {d['source']}]\n{d['content']}"
        for d in relevant
    )

    user_message = f"""Câu hỏi: {question}

Tài liệu kỹ thuật tham khảo:
{context_text if context_text else "(không có tài liệu phù hợp)"}

Hãy trả lời dựa trên tài liệu trên và kiến thức chuyên môn."""

    client   = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return {
        "answer":         response.content[0].text,
        "sources":        [d["source"] for d in relevant],
        "context_chunks": len(relevant),
    }


def build_diagnosis_query(
    disease: str | None,
    ph: float | None,
    salinity: float | None,
    temperature: float | None,
    area_ha: float | None,
    calc_recommendation: dict | None,
) -> str:
    parts = []
    if disease:
        parts.append(f"tôm/cua bị {disease}")
    if ph is not None:
        parts.append(f"pH = {ph}")
    if salinity is not None:
        parts.append(f"độ mặn = {salinity} ppt")
    if temperature is not None:
        parts.append(f"nhiệt độ = {temperature}°C")
    if area_ha:
        parts.append(f"diện tích = {area_ha} ha")
    if calc_recommendation:
        w = (calc_recommendation.get("lime") or {}).get("warning")
        if w:
            parts.append(f"cảnh báo pH: {w}")

    ctx = ", ".join(parts) if parts else "tình trạng ao nuôi"
    return f"Tôi cần hướng dẫn xử lý: {ctx}. Đưa ra phác đồ điều trị và phòng ngừa cụ thể."
