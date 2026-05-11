# 🎮 TicTacToe AI – Minimax + Alpha-Beta Pruning

Ứng dụng chơi Tic-Tac-Toe hoàn chỉnh với AI thông minh, viết bằng Python + PyQt6.

---

## 📦 Sử dụng bản Release (Chạy ngay không cần cài đặt)

Nếu bạn chỉ muốn trải nghiệm game mà không cần cài đặt môi trường Python, hãy tải các phiên bản đã được đóng gói sẵn tại trang **Releases** của kho lưu trữ này:

- **🪟 Windows:** 1. Tải file zip dành cho Windows và giải nén.
  2. Nhấp đúp vào file `main.exe` (hoặc file `.exe` tương ứng) để mở game. 
  *(Lưu ý: Nếu Windows SmartScreen hiện thông báo bảo vệ màu xanh, hãy nhấn **More info** > **Run anyway**).*
- **🐧 Linux:** 1. Tải file `.AppImage` về máy.
  2. Cấp quyền thực thi: Nhấp chuột phải vào file > **Properties** > tab **Permissions** > Tích chọn **Allow executing file as program**. (Hoặc mở Terminal gõ `chmod +x ten_file.AppImage`).
  3. Nhấp đúp vào file để mở ứng dụng.
- **🍏 macOS:** 1. Tải file nén dành cho macOS và giải nén.
  2. Lần đầu tiên chạy, nếu hệ thống Apple Gatekeeper chặn ứng dụng, hãy nhấp **Chuột phải** vào file ứng dụng và chọn **Open** (Mở).

## 📋 Yêu cầu hệ thống

- **Python** ≥ 3.9
- **PyQt6** ≥ 6.4.0

---

## 🚀 Cài đặt & Chạy

```bash
# 1. Cài thư viện
pip install PyQt6

# 2. Chạy ứng dụng
python main.py
```

---

## 🗂️ Cấu trúc dự án

```
tictactoe/
├── main.py          # Điểm khởi động
├── constants.py     # Hằng số, màu sắc, bảng depth
├── game.py          # Logic cốt lõi (Board, GameState)
├── ai.py            # AI Engine (Minimax + Alpha-Beta + Heuristic)
├── ui_main.py       # Cửa sổ chính
├── ui_board.py      # Widget vẽ bàn cờ + heatmap
├── ui_settings.py   # Dialog cài đặt
└── requirements.txt
```

---

## 🎯 Tính năng

### Chế độ chơi
| Chế độ | Mô tả |
|--------|-------|
| 🧑 vs 🧑 | Hai người chơi trên cùng máy |
| 🧑 vs 🤖 | Người chơi với AI |
| 🤖 vs 🤖 | Hai AI đấu nhau (chế độ huấn luyện) |

### Cài đặt ván chơi
- **Kích thước bàn cờ**: 3×3 đến 16×16
- **Số quân liên tiếp để thắng**: tự động đề xuất theo kích thước
- **Số hiệp thắng**: 1 đến 20
- **Người đi trước**: Người chơi 1 hoặc 2
- **Độ khó AI**: Dễ / Trung bình / Khó / Siêu khó

### Chế độ Máy vs Máy
- ⏸ **Tạm dừng / Tiếp tục** tự do
- ✅ **Bật/tắt từng máy** riêng lẻ (Máy 1, Máy 2, hoặc cả hai)
- Độ khó có thể đặt khác nhau cho mỗi máy

### Heatmap trọng số AI
- Các ô đang được AI đánh giá hiển thị màu gradient (lạnh → nóng)
- Trọng số hiển thị trực tiếp trên ô
- Ô bị **cắt tỉa Alpha-Beta** hiển thị màu tím + ký hiệu ✂
- Có thể bật/tắt hiển thị heatmap

---

## 🧠 Thuật toán AI

### Minimax + Alpha-Beta Pruning
```
minimax(board, depth, α, β, maximizing):
    if terminal or depth == 0:
        return heuristic_eval(board)
    
    candidates = get_candidate_moves(radius=2)  # Tối ưu: chỉ xét ô gần quân đã đánh
    sort_by_heuristic(candidates)               # Sắp xếp để cắt tỉa nhiều hơn
    
    for move in candidates:
        play(move)
        val = minimax(board, depth-1, α, β, not maximizing)
        undo(move)
        
        if maximizing:
            α = max(α, val)
            if α >= β: prune()  # Beta cutoff
        else:
            β = min(β, val)
            if β <= α: prune()  # Alpha cutoff
```

### Hàm đánh giá Heuristic
Quét 4 hướng (→ ↓ ↘ ↗), tính điểm theo:
- Số quân liên tiếp (2, 3, 4, 5+)
- Số đầu mở (0, 1, 2)

| Chuỗi | 2 đầu mở | 1 đầu mở |
|-------|----------|----------|
| 2 quân | 10 | 5 |
| 3 quân | 1,000 | 100 |
| 4 quân | 50,000 | 5,000 |
| ≥win_len | 1,000,000 | 1,000,000 |

### Tối ưu hoá
1. **Candidate moves**: Chỉ xét ô trống trong bán kính 2 quanh quân đã đánh
2. **Move ordering**: Sắp xếp ứng viên theo điểm heuristic nhanh trước khi duyệt
3. **Alpha-Beta Pruning**: Cắt bỏ nhánh không cần duyệt
4. **Thread riêng**: AI chạy trong background thread, UI không bị đơ

### Độ sâu tìm kiếm (depth) theo độ khó

| Kích thước | Dễ | Trung bình | Khó | Siêu khó |
|-----------|-----|------------|-----|----------|
| 3×3 | 1 | 3 | 6 | 9 (toàn bộ) |
| 4×4 | 1 | 2 | 4 | 6 |
| 5×5 | 1 | 2 | 3 | 5 |
| 6-8 | 1 | 2 | 3 | 4 |
| 9-13 | 1 | 2 | 3 | 3 |
| 14-16 | 1 | 2 | 2 | 2 |

---

## 🔌 Mở rộng cho Machine Learning

File `game.py` và `ai.py` được thiết kế tách biệt khỏi UI:

```python
from game import GameConfig, GameState, Board
from ai import AIEngine

# Tạo environment
config = GameConfig(board_size=10, win_length=5, mode="cvc")
state  = GameState(config)

# Chạy episode
while not state.game_over:
    board = state.board
    action = your_ml_agent.predict(board.grid)
    state.make_move(*action)

reward = 1 if state.winner == YOUR_PLAYER else -1
```

Bạn có thể:
- Thay `AIEngine` bằng DQN / Policy Gradient / AlphaZero
- Dùng `Board.get_candidate_moves()` làm action space
- Dùng `evaluate_board()` làm reward shaping
- Thu thập data từ chế độ CVC để supervised learning

---

## 🎨 Giao diện

- Dark theme hiện đại với palette tím/hồng
- Bàn cờ co giãn theo cửa sổ
- Highlight ô thắng màu vàng + đường kẻ
- Ô cuối cùng vừa đánh được đánh dấu
- Card người chơi sáng lên khi đến lượt
