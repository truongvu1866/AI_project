# ============================================================
#  game.py – Logic cốt lõi: bàn cờ, kiểm tra thắng, trạng thái
# ============================================================
from __future__ import annotations
from typing import Optional, List, Tuple

from constants import (
    EMPTY, PLAYER_1, PLAYER_2,
    MIN_BOARD, MAX_BOARD,
)


class GameConfig:
    """Cấu hình một ván chơi."""
    def __init__(
        self,
        board_size:   int = 3,
        win_length:   int = 3,
        mode:         str = "pvp",
        first_player: int = PLAYER_1,
        wins_needed:  int = 1,
        diff_ai1:     str = "Khó",
        diff_ai2:     str = "Khó",
        ai1_enabled:  bool = True,
        ai2_enabled:  bool = True,
    ):
        self.board_size   = max(MIN_BOARD, min(MAX_BOARD, board_size))
        self.win_length   = win_length
        self.mode         = mode
        self.first_player = first_player
        self.wins_needed  = wins_needed
        self.diff_ai1     = diff_ai1
        self.diff_ai2     = diff_ai2
        self.ai1_enabled  = ai1_enabled   # chỉ dùng ở CVC: bật/tắt AI1
        self.ai2_enabled  = ai2_enabled   # chỉ dùng ở CVC: bật/tắt AI2


class Board:
    """Bàn cờ và các thao tác cơ bản."""

    DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]  # →, ↓, ↘, ↗

    def __init__(self, size: int, win_length: int):
        self.size       = size
        self.win_length = win_length
        self.grid: List[List[int]] = [[EMPTY] * size for _ in range(size)]
        self.move_count = 0
        self.last_move: Optional[Tuple[int, int]] = None

    # ── Cơ bản ──────────────────────────────────────────────
    def copy(self) -> "Board":
        b = Board(self.size, self.win_length)
        b.grid       = [row[:] for row in self.grid]
        b.move_count = self.move_count
        b.last_move  = self.last_move
        return b

    def place(self, row: int, col: int, player: int) -> bool:
        if self.grid[row][col] != EMPTY:
            return False
        self.grid[row][col] = player
        self.move_count += 1
        self.last_move = (row, col)
        return True

    def undo(self, row: int, col: int):
        self.grid[row][col] = EMPTY
        self.move_count -= 1
        self.last_move = None

    def is_full(self) -> bool:
        return self.move_count == self.size * self.size

    def is_empty_cell(self, r: int, c: int) -> bool:
        return self.grid[r][c] == EMPTY

    # ── Kiểm tra thắng ──────────────────────────────────────
    def check_winner(self) -> Optional[int]:
        """Kiểm tra toàn bàn cờ, trả về người thắng hoặc None."""
        if self.last_move is None:
            return None
        return self._check_from(self.last_move[0], self.last_move[1])

    def _check_from(self, row: int, col: int) -> Optional[int]:
        player = self.grid[row][col]
        if player == EMPTY:
            return None
        for dr, dc in self.DIRECTIONS:
            count = 1 + self._count_dir(row, col, dr, dc, player) \
                      + self._count_dir(row, col, -dr, -dc, player)
            if count >= self.win_length:
                return player
        return None

    def _count_dir(self, r, c, dr, dc, player) -> int:
        count = 0
        r += dr; c += dc
        while 0 <= r < self.size and 0 <= c < self.size \
              and self.grid[r][c] == player:
            count += 1
            r += dr; c += dc
        return count

    def get_winning_cells(self, player: int) -> List[Tuple[int, int]]:
        """Trả về danh sách ô tạo nên chuỗi thắng."""
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != player:
                    continue
                for dr, dc in self.DIRECTIONS:
                    cells = [(r, c)]
                    for step in range(1, self.win_length):
                        nr, nc = r + dr * step, c + dc * step
                        if 0 <= nr < self.size and 0 <= nc < self.size \
                                and self.grid[nr][nc] == player:
                            cells.append((nr, nc))
                        else:
                            break
                    if len(cells) >= self.win_length:
                        return cells
        return []

    # ── Các ô ứng viên (cho AI) ──────────────────────────────
    def get_candidate_moves(self, radius: int = 2) -> List[Tuple[int, int]]:
        """
        Trả về các ô trống nằm trong vùng bán kính `radius` quanh
        bất kỳ ô đã đánh nào. Nếu bàn cờ trống, chọn tâm.
        """
        if self.move_count == 0:
            center = self.size // 2
            return [(center, center)]

        candidates = set()
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != EMPTY:
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.size and 0 <= nc < self.size \
                                    and self.grid[nr][nc] == EMPTY:
                                candidates.add((nr, nc))
        return list(candidates)

    def get_neighbors_8dir(self, row: int, col: int,
                           radius: int = 2) -> List[Tuple[int, int]]:
        """Các ô trống theo 8 hướng trong bán kính."""
        result = []
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.size and 0 <= nc < self.size \
                        and self.grid[nr][nc] == EMPTY:
                    result.append((nr, nc))
        return result


class GameState:
    """Quản lý trạng thái một ván (match gồm nhiều hiệp)."""

    def __init__(self, config: GameConfig):
        self.config  = config
        self.score   = {PLAYER_1: 0, PLAYER_2: 0}
        self.current_game = 1
        self._new_game()

    def _new_game(self):
        self.board          = Board(self.config.board_size,
                                    self.config.win_length)
        self.current_player = self.config.first_player
        self.winner: Optional[int] = None
        self.is_draw        = False
        self.game_over      = False
        self.winning_cells: List[Tuple[int, int]] = []

    def make_move(self, row: int, col: int) -> bool:
        if self.game_over:
            return False
        if not self.board.place(row, col, self.current_player):
            return False
        winner = self.board.check_winner()
        if winner:
            self.winner       = winner
            self.winning_cells = self.board.get_winning_cells(winner)
            self.score[winner] += 1
            self.game_over    = True
        elif self.board.is_full():
            self.is_draw   = True
            self.game_over = True
        else:
            self.current_player = PLAYER_2 \
                if self.current_player == PLAYER_1 else PLAYER_1
        return True

    def next_game(self):
        """Bắt đầu hiệp tiếp theo (đổi người đi trước)."""
        self.current_game += 1
        first = PLAYER_2 \
            if self.config.first_player == PLAYER_1 else PLAYER_1
        self.config.first_player = first
        self._new_game()

    def match_winner(self) -> Optional[int]:
        needed = self.config.wins_needed
        for p in (PLAYER_1, PLAYER_2):
            if self.score[p] >= needed:
                return p
        return None

    @property
    def is_match_over(self) -> bool:
        return self.match_winner() is not None
