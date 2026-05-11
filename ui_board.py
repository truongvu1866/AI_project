# ============================================================
#  ui_board.py – Widget vẽ bàn cờ + heatmap trọng số AI
# ============================================================
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont,
)
from PyQt6.QtWidgets import QWidget, QSizePolicy

from constants import (
    EMPTY, PLAYER_1, COLOR_BG2, COLOR_BORDER, COLOR_HOVER,
    COLOR_PLAYER1, COLOR_PLAYER2, COLOR_WIN_CELL,
    COLOR_ACCENT1,
)


def _lerp_color(c1: QColor, c2: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        int(c1.red()   + (c2.red()   - c1.red())   * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue()  + (c2.blue()  - c1.blue())  * t),
    )


class BoardWidget(QWidget):
    """
    Widget vẽ bàn cờ Tic-Tac-Toe.
    Phát tín hiệu cell_clicked(row, col) khi người dùng click.
    """
    cell_clicked = pyqtSignal(int, int)

    # Palette heatmap
    _COLD   = QColor("#0d2b45")
    _WARM   = QColor("#8b3a0f")
    _HOT    = QColor("#c0392b")
    _PRUNED = QColor("#1a1a3a")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setMinimumSize(300, 300)

        # State
        self._board_data: List[List[int]] = []
        self._size       = 3
        self._win_cells: List[Tuple[int, int]] = []
        self._hover: Optional[Tuple[int, int]] = None
        self._interactive = True

        # Heatmap
        self._heatmap: Dict[Tuple[int, int], float] = {}
        self._pruned:  List[Tuple[int, int]] = []
        self._show_heatmap = False
        self._last_move: Optional[Tuple[int, int]] = None

    # ── Cập nhật trạng thái ─────────────────────────────────
    def set_board(self, grid: List[List[int]], size: int,
                  win_cells: List[Tuple[int,int]] = None,
                  last_move: Tuple[int,int] = None):
        self._board_data = grid
        self._size       = size
        self._win_cells  = win_cells or []
        self._last_move  = last_move
        self.update()

    def set_heatmap(self, heatmap: Dict[Tuple[int,int], float],
                    pruned: List[Tuple[int,int]]):
        self._heatmap = heatmap
        self._pruned  = pruned
        self.update()

    def clear_heatmap(self):
        self._heatmap = {}
        self._pruned  = []
        self.update()

    def set_show_heatmap(self, show: bool):
        self._show_heatmap = show
        self.update()

    def set_interactive(self, v: bool):
        self._interactive = v

    # ── Geometry helpers ────────────────────────────────────
    def _cell_size(self) -> float:
        pad = 24
        w = (self.width()  - pad * 2) / self._size
        h = (self.height() - pad * 2) / self._size
        return min(w, h)

    def _origin(self) -> Tuple[float, float]:
        cs  = self._cell_size()
        pad = 24
        ox  = (self.width()  - cs * self._size) / 2
        oy  = (self.height() - cs * self._size) / 2
        return ox, oy

    def _cell_rect(self, row: int, col: int) -> QRect:
        cs = self._cell_size()
        ox, oy = self._origin()
        return QRect(int(ox + col * cs), int(oy + row * cs),
                     int(cs), int(cs))

    def _cell_at(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        cs = self._cell_size()
        ox, oy = self._origin()
        col = int((px - ox) / cs)
        row = int((py - oy) / cs)
        if 0 <= row < self._size and 0 <= col < self._size:
            return row, col
        return None

    # ── Events ──────────────────────────────────────────────
    def mouseMoveEvent(self, ev):
        if not self._interactive:
            return
        cell = self._cell_at(ev.position().x(), ev.position().y())
        if cell != self._hover:
            self._hover = cell
            self.update()

    def leaveEvent(self, ev):
        self._hover = None
        self.update()

    def mousePressEvent(self, ev):
        if not self._interactive:
            return
        if ev.button() == Qt.MouseButton.LeftButton:
            cell = self._cell_at(ev.position().x(), ev.position().y())
            if cell:
                self.cell_clicked.emit(*cell)

    # ── Paint ───────────────────────────────────────────────
    def paintEvent(self, _):
        if not self._board_data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_background(p)
        self._draw_grid(p)
        self._draw_heatmap(p)
        self._draw_pieces(p)
        self._draw_win_line(p)
        p.end()

    def _draw_background(self, p: QPainter):
        cs  = self._cell_size()
        ox, oy = self._origin()
        rect = QRect(int(ox) - 2, int(oy) - 2,
                     int(cs * self._size) + 4,
                     int(cs * self._size) + 4)
        p.setPen(QPen(QColor(COLOR_BORDER), 2))
        p.setBrush(QBrush(QColor(COLOR_BG2)))
        p.drawRoundedRect(rect, 8, 8)

    def _draw_grid(self, p: QPainter):
        cs  = self._cell_size()
        ox, oy = self._origin()
        pen = QPen(QColor(COLOR_BORDER), 1)
        p.setPen(pen)
        for i in range(self._size + 1):
            x = int(ox + i * cs)
            y = int(oy + i * cs)
            p.drawLine(x, int(oy), x, int(oy + self._size * cs))
            p.drawLine(int(ox), y, int(ox + self._size * cs), y)

    def _draw_heatmap(self, p: QPainter):
        if not self._show_heatmap:
            return

        # Normalize scores
        vals = list(self._heatmap.values())
        if vals:
            mn, mx = min(vals), max(vals)
            rng = mx - mn if mx != mn else 1
        else:
            mn, mx, rng = 0, 1, 1

        font = QFont("Monospace", max(6, int(self._cell_size() * 0.18)))
        p.setFont(font)

        # Pruned cells (background only)
        for (r, c) in self._pruned:
            rect = self._cell_rect(r, c)
            if self._board_data and self._board_data[r][c] != EMPTY:
                continue
            p.setBrush(QBrush(self._PRUNED))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(rect)
            p.setPen(QPen(QColor("#444466"), 1))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "✂")

        # Evaluated cells
        for (r, c), score in self._heatmap.items():
            if self._board_data and self._board_data[r][c] != EMPTY:
                continue
            t = (score - mn) / rng
            if t < 0.5:
                color = _lerp_color(self._COLD, self._WARM, t * 2)
            else:
                color = _lerp_color(self._WARM, self._HOT, (t - 0.5) * 2)
            color.setAlpha(180)
            rect = self._cell_rect(r, c)
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(rect)

            # Hiển thị trọng số
            p.setPen(QPen(QColor(255, 255, 255, 200)))
            label = self._fmt_score(score)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    @staticmethod
    def _fmt_score(v: float) -> str:
        av = abs(v)
        if av >= 1_000_000: return f"{'±' if v < 0 else ''}∞"
        if av >= 1_000:     return f"{v/1000:.1f}k"
        return f"{v:.0f}"

    def _draw_pieces(self, p: QPainter):
        cs = self._cell_size()
        margin = cs * 0.18

        for r in range(self._size):
            for c in range(self._size):
                val = self._board_data[r][c] if self._board_data else EMPTY
                rect = self._cell_rect(r, c)

                # Hover highlight
                if self._hover == (r, c) and val == EMPTY and self._interactive:
                    p.setBrush(QBrush(QColor(COLOR_HOVER)))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawRect(rect)

                # Last move indicator
                if self._last_move == (r, c) and val != EMPTY:
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.setPen(QPen(QColor(COLOR_ACCENT1), 2))
                    inner = rect.adjusted(3, 3, -3, -3)
                    p.drawRect(inner)

                if val == EMPTY:
                    continue

                inner = QRect(
                    int(rect.x() + margin),
                    int(rect.y() + margin),
                    int(rect.width()  - margin * 2),
                    int(rect.height() - margin * 2),
                )

                if val == PLAYER_1:
                    self._draw_x(p, inner)
                else:
                    self._draw_o(p, inner)

    def _draw_x(self, p: QPainter, rect: QRect):
        color = QColor(COLOR_PLAYER1)
        lw = max(2, int(rect.width() * 0.12))
        pen = QPen(color, lw, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        pad = lw
        p.drawLine(rect.x() + pad, rect.y() + pad,
                   rect.right() - pad, rect.bottom() - pad)
        p.drawLine(rect.right() - pad, rect.y() + pad,
                   rect.x() + pad, rect.bottom() - pad)

    def _draw_o(self, p: QPainter, rect: QRect):
        color = QColor(COLOR_PLAYER2)
        lw = max(2, int(rect.width() * 0.12))
        pen = QPen(color, lw, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        pad = lw // 2
        p.drawEllipse(rect.adjusted(pad, pad, -pad, -pad))

    def _draw_win_line(self, p: QPainter):
        if not self._win_cells:
            return
        cs = self._cell_size()
        # Highlight win cells
        for (r, c) in self._win_cells:
            rect = self._cell_rect(r, c)
            color = QColor(COLOR_WIN_CELL)
            color.setAlpha(60)
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(rect)

        # Line qua tâm các ô đầu-cuối
        if len(self._win_cells) >= 2:
            def center(r, c):
                rect = self._cell_rect(r, c)
                return QPoint(rect.center().x(), rect.center().y())

            c1 = center(*self._win_cells[0])
            c2 = center(*self._win_cells[-1])
            pen = QPen(QColor(COLOR_WIN_CELL), max(3, int(cs * 0.08)),
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(c1, c2)
