# Label Schema — Nhãn bệnh tôm sú & cua biển

## Tôm sú (Black Tiger Shrimp) — 7 lớp

| ID | Nhãn | Tên tiếng Anh | Triệu chứng nhận biết |
|----|------|---------------|----------------------|
| 0 | `healthy_shrimp` | Healthy Shrimp | Màu sắc tự nhiên, hoạt động bình thường |
| 1 | `black_gill` | Black Gill Disease | Mang chuyển màu đen, nâu xỉn |
| 2 | `white_spot` | White Spot Syndrome (WSSV) | Đốm trắng trên vỏ, đầu ngực |
| 3 | `red_body` | Red Body Disease | Thân đỏ hồng bất thường, đuôi đỏ |
| 4 | `soft_shell` | Soft Shell Syndrome | Vỏ mềm, không cứng sau lột xác |
| 5 | `empty_gut` | Empty Gut (EHP) | Ruột không có thức ăn, nhạt màu |
| 6 | `yellow_head` | Yellow Head Virus (YHV) | Đầu vàng, gan tụy vàng |

## Cua biển (Mud Crab) — 5 lớp

| ID | Nhãn | Tên tiếng Anh | Triệu chứng nhận biết |
|----|------|---------------|----------------------|
| 7 | `healthy_crab` | Healthy Crab | Màu sắc tươi, hoạt động linh hoạt |
| 8 | `black_gill_crab` | Black Gill Crab | Mang đen, hôi, kém ăn |
| 9 | `barnacle` | Barnacle/Fouling | Vỏ mai đóng rong, hà |
| 10 | `limb_loss` | Limb Loss | Mất càng, gãy chân, yếu ớt |
| 11 | `fungal_crab` | Fungal Infection | Đốm trắng/vàng trên mai, ăn mòn |

## Hướng dẫn gán nhãn

- **Bounding box:** Khoanh sát phần cơ thể tôm/cua, không gồm nền ao
- **Ưu tiên:** Nếu 1 con mắc nhiều bệnh, gán nhãn bệnh nặng nhất
- **Ảnh không rõ:** Bỏ qua, không gán nhãn — tránh nhiễu dữ liệu
- **Góc chụp:** Ghi chú góc chụp trong metadata (top, side, underwater)
