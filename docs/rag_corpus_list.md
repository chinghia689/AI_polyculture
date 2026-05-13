# Danh sách tài liệu kỹ thuật cho RAG Corpus

## Ưu tiên 1 — Tải tự động được (có URL trực tiếp)

Chạy: `python scripts/download_documents.py`

| # | Tài liệu | Nguồn | Ngôn ngữ | URL |
|---|---------|-------|---------|-----|
| 1 | Mud Crab Aquaculture (FAO Technical Paper 567) | FAO | EN | https://www.fao.org/4/ba0110e/ba0110e.pdf |
| 2 | Capture-Based Aquaculture of Mud Crabs (Scylla spp.) | FAO | EN | https://www.fao.org/4/i0254e/i0254e13.pdf |
| 3 | Shrimp AHPND Strategy Manual | FAO | EN | https://openknowledge.fao.org/server/api/core/bitstreams/af15fde4-ac7a-4352-be4e-3eb0e0aa8685/content |
| 4 | Internal & External Anatomy of Penaeid Shrimp | FAO | EN | https://www.fao.org/4/y1679e/y1679e04.pdf |
| 5 | Seed Production of Mud Crab Scylla spp. | NACA | EN | https://library.enaca.org/AquacultureAsia/Articles/July-Sept-2002/Seed_production_mudcrab.pdf |
| 6 | The Role of Probiotics in Vannamei Shrimp Aquaculture | Veterinary World | EN | https://www.veterinaryworld.org/Vol.16/March-2023/26.pdf |
| 7 | Evolution of Shrimp Systems: Bangladesh & Vietnam | WorldFish | EN | https://digitalarchive.worldfishcenter.org/bitstreams/78276259-b0e8-4896-a6bd-907075cbfa3a/download |
| 8 | Integrated Mangrove-Fishery Farming System | IUCN | EN | https://iucn.org/sites/default/files/content/documents/2016/imffs_sgf_project_report.pdf |

## Ưu tiên 2 — Tải thủ công (cần đăng nhập / xin file)

| # | Tài liệu | Nguồn | Cách lấy |
|---|---------|-------|---------|
| 9 | Polyculture of Mud Crab in Region 3 | SEAFDEC | https://repository.seafdec.org/handle/20.500.12066/5275 → Download |
| 10 | Selection of Probiotics for Shrimp Hatcheries | SEAFDEC | https://repository.seafdec.org/handle/20.500.12066/5198 → Download |
| 11 | Integrated Shrimp-Mangrove Farming — Mekong Delta | ResearchGate | Đăng ký ResearchGate miễn phí → Download |
| 12 | Management of Integrated Mangrove-Aquaculture | ResearchGate | Đăng ký ResearchGate miễn phí → Download |

## Ưu tiên 3 — Tài liệu tiếng Việt (thu thập thủ công)

| # | Tài liệu | Nguồn | Cách lấy |
|---|---------|-------|---------|
| 13 | Quy trình kỹ thuật nuôi tôm sú thương phẩm | Sở NN&PTNT Cà Mau | Liên hệ trực tiếp hoặc website tỉnh |
| 14 | Kỹ thuật nuôi cua biển xen kẽ tôm sú | Trung tâm Khuyến nông QG | khuyennong.gov.vn → Tìm kiếm |
| 15 | Bệnh thường gặp & biện pháp phòng trị tôm sú | RIA2 / Viện NCNTTS II | ria2.gov.vn |

## Sau khi tải về

1. Lưu tất cả PDF vào `module_rag/data/documents/`
2. Đặt tên: `[priority]_[topic]_[source]_[year].pdf`
3. Chạy ingest: `python scripts/ingest_documents.py`
