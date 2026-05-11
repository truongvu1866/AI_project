# ============================================================
#  ai.py – AI Minimax + Alpha-Beta Pruning + Heuristic
# ============================================================
from __future__ import annotations

import math
import threading
from typing import Optional, Tuple, Dict, List, Callable

from constants import EMPTY, PLAYER_1, PLAYER_2, get_depth
from game import Board

# ─────────────────────────────────────────────────────────────
#  Hàm đánh giá Heuristic
# ─────────────────────────────────────────────────────────────
# Trọng số theo số quân liên tiếp (open = 2 đầu mở, half = 1 đầu mở)
SCORE_TABLE = {
    # (count, open_ends): score
    (2, 2): 10,
    (2, 1): 5,
    (3, 2): 1000,
    (3, 1): 100,
    (4, 2): 50000,
    (4, 1): 5000,
    (5, 2): 500000,
    (5, 1): 500000,
    (6, 2): 500000,
    (6, 1): 500000,
}


def _score_line(count: int, open_ends: int, win_length: int) -> int:
    if count >= win_length:
        return 1_000_000
    key = (count, open_ends)
    return SCORE_TABLE.get(key, 0)


def evaluate_board(board: Board, ai_player: int) -> int:
    """
    Đánh giá toàn bộ bàn cờ theo quan điểm của ai_player.
    Quét 4 hướng, đếm chuỗi liên tiếp cho mỗi người chơi.
    """
    opponent = PLAYER_2 if ai_player == PLAYER_1 else PLAYER_1
    ai_score  = 0
    opp_score = 0

    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    size = board.size
    win  = board.win_length

    for r in range(size):
        for c in range(size):
            for dr, dc in directions:
                # Chỉ bắt đầu chuỗi mới từ điểm khởi đầu
                pr, pc = r - dr, c - dc
                if 0 <= pr < size and 0 <= pc < size:
                    continue  # đã đếm rồi

                # Đếm chuỗi
                player = board.grid[r][c]
                if player == EMPTY:
                    continue
                count = 0
                nr, nc = r, c
                while 0 <= nr < size and 0 <= nc < size \
                        and board.grid[nr][nc] == player:
                    count += 1
                    nr += dr; nc += dc

                # Kiểm tra 2 đầu
                open_ends = 0
                # Đầu trước
                br, bc = r - dr, c - dc
                if 0 <= br < size and 0 <= bc < size \
                        and board.grid[br][bc] == EMPTY:
                    open_ends += 1
                # Đầu sau
                if 0 <= nr < size and 0 <= nc < size \
                        and board.grid[nr][nc] == EMPTY:
                    open_ends += 1

                s = _score_line(count, open_ends, win)
                if player == ai_player:
                    ai_score += s
                else:
                    opp_score += s

    return ai_score - opp_score


def evaluate_position(board: Board, row: int, col: int,
                       player: int, win_length: int) -> int:
    """Đánh giá ô (row,col) cho player – dùng khi chọn ứng viên."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    total = 0
    for dr, dc in directions:
        count = 1
        open_ends = 0
        for sign in (1, -1):
            r2, c2 = row + sign * dr, col + sign * dc
            while 0 <= r2 < board.size and 0 <= c2 < board.size \
                    and board.grid[r2][c2] == player:
                count += 1
                r2 += sign * dr; c2 += sign * dc
            if 0 <= r2 < board.size and 0 <= c2 < board.size \
                    and board.grid[r2][c2] == EMPTY:
                open_ends += 1
        total += _score_line(count, open_ends, win_length)
    return total


# ─────────────────────────────────────────────────────────────
#  AIMove – kết quả trả về của AI
# ─────────────────────────────────────────────────────────────
class AIMove:
    def __init__(self):
        self.row:     int   = -1
        self.col:     int   = -1
        self.score:   int   = 0
        # Heatmap: dict (r,c) -> score  (các ô đã xét ở tầng 1)
        self.heatmap: Dict[Tuple[int,int], float] = {}
        # Ô bị cắt tỉa
        self.pruned:  List[Tuple[int,int]] = []


# ─────────────────────────────────────────────────────────────
#  Lớp AI
# ─────────────────────────────────────────────────────────────
class AIEngine:
    """
    Minimax + Alpha-Beta Pruning + Heuristic evaluation.
    Chỉ xét ứng viên trong bán kính 2 quanh các ô đã đánh.
    """

    def __init__(self, player: int, difficulty: str):
        self.player     = player
        self.opponent   = PLAYER_2 if player == PLAYER_1 else PLAYER_1
        self.difficulty = difficulty
        self.nodes_visited = 0
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()

    def reset(self):
        self._stop_flag.clear()

    def get_move(self, board: Board,
                 on_heatmap: Optional[Callable] = None) -> AIMove:
        """Tính nước đi tốt nhất. Gọi on_heatmap(heatmap, pruned) khi xong."""
        self.reset()
        self.nodes_visited = 0
        depth = get_depth(board.size, self.difficulty)
        result = AIMove()

        candidates = board.get_candidate_moves(radius=2)
        if not candidates:
            return result

        # Nếu chỉ 1 ứng viên → đi ngay
        if len(candidates) == 1:
            result.row, result.col = candidates[0]
            return result

        best_score  = -math.inf
        heatmap     = {}
        pruned_list = []
        alpha       = -math.inf
        beta        = math.inf

        # Sắp xếp ứng viên để cắt tỉa hiệu quả hơn
        candidates = self._order_moves(board, candidates, self.player)

        for (r, c) in candidates:
            if self._stop_flag.is_set():
                break
            board.place(r, c, self.player)
            score = self._minimax(board, depth - 1, alpha, beta,
                                  False, pruned_list)
            board.undo(r, c)
            board.last_move = None

            heatmap[(r, c)] = score
            if score > best_score:
                best_score     = score
                result.row     = r
                result.col     = c
                result.score   = score
            alpha = max(alpha, best_score)

        result.heatmap = heatmap
        result.pruned  = pruned_list

        if on_heatmap:
            on_heatmap(heatmap, pruned_list)

        return result

    def _minimax(self, board: Board, depth: int,
                 alpha: float, beta: float,
                 is_maximizing: bool,
                 pruned_list: list) -> float:
        self.nodes_visited += 1

        # Kiểm tra terminal
        winner = board.check_winner()
        if winner == self.player:
            return 1_000_000 + depth        # Thắng sớm = tốt hơn
        if winner == self.opponent:
            return -1_000_000 - depth
        if board.is_full() or depth == 0:
            return evaluate_board(board, self.player)

        candidates = board.get_candidate_moves(radius=2)
        if not candidates:
            return evaluate_board(board, self.player)

        current = self.player if is_maximizing else self.opponent
        candidates = self._order_moves(board, candidates, current)

        if is_maximizing:
            value = -math.inf
            for (r, c) in candidates:
                if self._stop_flag.is_set():
                    return value
                board.place(r, c, current)
                child_val = self._minimax(board, depth - 1,
                                          alpha, beta, False, pruned_list)
                board.undo(r, c)
                board.last_move = None
                value = max(value, child_val)
                alpha = max(alpha, value)
                if alpha >= beta:
                    # Cắt tỉa Beta – ghi nhận các ô còn lại
                    pruned_list.extend(
                        m for m in candidates
                        if m != (r, c) and m not in pruned_list
                    )
                    break
            return value
        else:
            value = math.inf
            for (r, c) in candidates:
                if self._stop_flag.is_set():
                    return value
                board.place(r, c, current)
                child_val = self._minimax(board, depth - 1,
                                          alpha, beta, True, pruned_list)
                board.undo(r, c)
                board.last_move = None
                value = min(value, child_val)
                beta  = min(beta, value)
                if beta <= alpha:
                    pruned_list.extend(
                        m for m in candidates
                        if m != (r, c) and m not in pruned_list
                    )
                    break
            return value

    def _order_moves(self, board: Board,
                     moves: List[Tuple[int, int]],
                     player: int) -> List[Tuple[int, int]]:
        """
        Sắp xếp ứng viên theo điểm đánh giá nhanh –
        di chuyển có tiềm năng cao được xét trước giúp cắt tỉa nhiều hơn.
        """
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1

        def score_move(move):
            r, c = move
            # Giả lập đánh rồi đánh giá
            board.grid[r][c] = player
            s_player = evaluate_position(board, r, c, player, board.win_length)
            board.grid[r][c] = opponent
            s_opp = evaluate_position(board, r, c, opponent, board.win_length)
            board.grid[r][c] = EMPTY
            return s_player + s_opp * 1.1   # ưu tiên chặn hơi nhỉnh hơn

        return sorted(moves, key=score_move, reverse=True)


# ─────────────────────────────────────────────────────────────
#  Chạy AI trong thread riêng
# ─────────────────────────────────────────────────────────────
class AIWorker(threading.Thread):
    """
    Chạy AIEngine.get_move() trong thread riêng để không block UI.
    Gọi callback(move: AIMove) khi hoàn tất.
    """

    def __init__(self, engine: AIEngine, board: Board,
                 callback: Callable[[AIMove], None],
                 heatmap_callback: Optional[Callable] = None):
        super().__init__(daemon=True)
        self.engine   = engine
        self.board    = board.copy()
        self.callback = callback
        self.heatmap_callback = heatmap_callback

    def run(self):
        move = self.engine.get_move(self.board, self.heatmap_callback)
        self.callback(move)
