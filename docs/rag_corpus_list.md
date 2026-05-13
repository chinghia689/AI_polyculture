# Danh sách tài liệu kỹ thuật cho RAG Corpus

## Ưu tiên 1 — Tải tự động được (có URL trực tiếp)

Chạy: `python scripts/download_documents.py`

| # | Tài liệu | Nguồn | Ngôn ngữ | URL |
|---|---------|-------|---------|-----|
| 1 | Mud Crab Aquaculture (FAO Technical Paper 567) | FAO | EN | https://www.fao.org/4/ba0110e/ba0110e.pdf |
| 2 | Capture-Based Aquaculture of Mud Crabs (Scylla spp.) | FAO | EN | https://www.fao.org/4/i0254e/i0254e13.pdf |
| 3 | Crustacean Diseases & Diagnostic Guide (Shrimp & Crab) | NACA | EN | https://library.enaca.org/NACA-Publications/ADG-CrustaceanDiseases.pdf |
| 4 | AHPND Diagnosis & Detection — WOAH Aquatic Manual 2023 | WOAH | EN | https://www.woah.org/fileadmin/Home/eng/Health_standards/aahm/current/2.2.01_AHPND.pdf |
| 5 | AHPND Chapter — WOAH Aquatic Manual (legacy) | WOAH | EN | https://www.woah.org/fileadmin/Home/eng/Health_standards/aahm/current/chapitre_ahpnd.pdf |
| 6 | Seed Production of Mud Crab Scylla spp. | NACA | EN | https://library.enaca.org/AquacultureAsia/Articles/July-Sept-2002/Seed_production_mudcrab.pdf |
| 7 | The Role of Probiotics in Shrimp Aquaculture | PubMed Central | EN | https://pmc.ncbi.nlm.nih.gov/articles/PMC10082739/pdf/vetworld-16-548.pdf |
| 8 | Evolution of Shrimp Systems: Bangladesh & Vietnam | WorldFish | EN | https://digitalarchive.worldfishcenter.org/bitstreams/78276259-b0e8-4896-a6bd-907075cbfa3a/download |
| 9 | Integrated Mangrove-Fishery Farming System | IUCN | EN | https://iucn.org/sites/default/files/content/documents/2016/imffs_sgf_project_report.pdf |
| 10 | Kỹ thuật nuôi thương phẩm tôm sú, cua biển và cá hói | RIMF | VI | https://www.rimf.org.vn/Media/Default/Bantin/2024/%E1%BA%A4n%20ph%E1%BA%A9m%20qu%C3%BD%204.2024-2.pdf |
| 11 | Kỹ thuật nuôi tôm sú kết hợp cá măng trong ao đất | RIMF | VI | https://www.rimf.org.vn/Media/Default/AnPham/%E1%BA%A4n%20ph%E1%BA%A9m%20qu%C3%BD%202.2025.pdf |
| 12 | Nuôi tôm-lúa ĐBSCL: hiện trạng, bệnh và năng suất tôm/cua/cá | RIA2 | VI | https://vienthuysan2.org.vn/wp-content/uploads/2022/05/pdf-1.pdf |
| 13 | Sự hiện diện của WSSV, Vibrio parahaemolyticus và EHP trên tôm giống và tôm nuôi nước lợ ở ĐBSCL | RIA2 | VI | https://vienthuysan2.org.vn/wp-content/uploads/2022/05/pdf-16.pdf |
| 14 | Sự hiện diện của WSSV, Vibrio parahaemolyticus và EHP trên tôm giống cung cấp cho ĐBSCL và tôm nuôi thương phẩm | RIA2 | VI | https://vienthuysan2.org.vn/wp-content/uploads/2022/07/TCNC_So-21-2021-2.pdf |

## Ưu tiên 2 — Tải thủ công (cần đăng nhập / xin file)

| # | Tài liệu | Nguồn | Cách lấy |
|---|---------|-------|---------|
| 15 | Polyculture of Mud Crab in Region 3 | SEAFDEC | https://repository.seafdec.org/handle/20.500.12066/5275 → Download |
| 16 | Selection of Probiotics for Shrimp Hatcheries | SEAFDEC | https://repository.seafdec.org/handle/20.500.12066/5198 → Download |
| 17 | Integrated Shrimp-Mangrove Farming — Mekong Delta | ResearchGate | Đăng ký ResearchGate miễn phí → Download |
| 18 | Management of Integrated Mangrove-Aquaculture | ResearchGate | Đăng ký ResearchGate miễn phí → Download |

## Ưu tiên 3 — Tài liệu tiếng Việt (thu thập thủ công)

| # | Tài liệu | Nguồn | Cách lấy |
|---|---------|-------|---------|
| 19 | Quy trình kỹ thuật nuôi tôm sú thương phẩm | Sở NN&PTNT Cà Mau | Liên hệ trực tiếp hoặc website tỉnh |
| 20 | Kỹ thuật nuôi cua biển xen kẽ tôm sú | Trung tâm Khuyến nông QG | khuyennong.gov.vn → Tìm kiếm |
| 21 | Bệnh thường gặp & biện pháp phòng trị tôm sú | RIA2 / Viện NCNTTS II | vienthuysan2.org.vn |

## Sau khi tải về

1. Lưu tất cả PDF vào `module_rag/data/documents/`
2. Đặt tên: `[priority]_[topic]_[source]_[year].pdf`
3. Chạy ingest: `python scripts/ingest_documents.py`
