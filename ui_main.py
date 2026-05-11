# ============================================================
#  ui_main.py – Cửa sổ chính: bố cục, điều phối game
# ============================================================
from __future__ import annotations
import time
from typing import Optional, Dict, Tuple, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QCheckBox, QSizePolicy, QSpacerItem, QProgressBar,
    QGroupBox, QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from constants import (
    MODE_PVP, MODE_PVC, MODE_CVC,
    PLAYER_1, PLAYER_2, EMPTY,
    PLAYER_SYMBOL,
    COLOR_BG, COLOR_BG2, COLOR_PANEL, COLOR_BORDER,
    COLOR_ACCENT1, COLOR_ACCENT2, COLOR_PLAYER1, COLOR_PLAYER2,
    CVC_DELAY_MS,
)
from game import GameConfig, GameState
from ai import AIEngine, AIWorker, AIMove
from ui_board import BoardWidget
from ui_settings import SettingsDialog


# ─────────────────────────────────────────────────────────────
MAIN_STYLE = f"""
QMainWindow, QWidget#central {{
    background: {COLOR_BG};
}}
QWidget {{
    color: #e0e0f0;
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
}}
QLabel#title {{
    font-size: 26px;
    font-weight: 900;
    letter-spacing: 4px;
    color: {COLOR_ACCENT1};
}}
QLabel#subtitle {{
    font-size: 11px;
    color: #666688;
    letter-spacing: 2px;
}}
QLabel#status {{
    font-size: 14px;
    font-weight: bold;
    padding: 8px 16px;
    border-radius: 8px;
    background: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    min-width: 260px;
}}
QLabel#score {{
    font-size: 13px;
    color: #c0c0e0;
}}
QGroupBox {{
    background: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    margin-top: 10px;
    color: #8888aa;
    font-weight: bold;
    font-size: 11px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {COLOR_ACCENT1};
}}
QPushButton.action {{
    border-radius: 7px;
    font-size: 12px;
    font-weight: bold;
    padding: 8px 18px;
    border: none;
}}
QPushButton#btnNew {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {COLOR_ACCENT1}, stop:1 {COLOR_ACCENT2});
    color: white;
}}
QPushButton#btnNew:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #9575ff, stop:1 #ff7599);
}}
QPushButton#btnSettings, QPushButton#btnReset, QPushButton#btnNext {{
    background: {COLOR_PANEL};
    color: #c0c0e0;
    border: 1px solid {COLOR_BORDER};
}}
QPushButton#btnSettings:hover, QPushButton#btnReset:hover,
QPushButton#btnNext:hover {{
    background: {COLOR_BORDER};
    color: white;
}}
QPushButton#btnPause {{
    background: #2a3a2a;
    color: #90ee90;
    border: 1px solid #3a5a3a;
}}
QPushButton#btnPause:hover {{ background: #3a4a3a; }}
QCheckBox {{
    color: #c0c0e0;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border-radius: 3px;
    border: 2px solid {COLOR_BORDER};
    background: {COLOR_BG2};
}}
QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT1};
    border-color: {COLOR_ACCENT1};
}}
QLabel#thinking {{
    color: {COLOR_ACCENT1};
    font-size: 12px;
    font-style: italic;
}}
"""


def _btn(text: str, obj_name: str, parent=None) -> QPushButton:
    b = QPushButton(text, parent)
    b.setObjectName(obj_name)
    b.setProperty("class", "action")
    return b


class PlayerCard(QFrame):
    """Thẻ hiển thị thông tin người chơi / AI."""
    def __init__(self, player: int, parent=None):
        super().__init__(parent)
        self.player = player
        symbol  = PLAYER_SYMBOL[player]
        color   = COLOR_PLAYER1 if player == PLAYER_1 else COLOR_PLAYER2
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_PANEL};
                border: 2px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 6px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setSpacing(4)

        self._lbl_sym = QLabel(symbol)
        self._lbl_sym.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_sym.setStyleSheet(f"font-size:28px;color:{color};font-weight:900;")
        lay.addWidget(self._lbl_sym)

        self._lbl_name = QLabel(f"Người chơi {player}")
        self._lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_name.setStyleSheet("font-size:11px;color:#8888aa;")
        lay.addWidget(self._lbl_name)

        self._lbl_score = QLabel("0")
        self._lbl_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_score.setStyleSheet(f"font-size:24px;font-weight:900;color:{color};")
        lay.addWidget(self._lbl_score)

        self._lbl_tag = QLabel("")
        self._lbl_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_tag.setStyleSheet("font-size:10px;color:#666688;")
        lay.addWidget(self._lbl_tag)
        self.setFixedWidth(130)

    def set_score(self, s: int):
        self._lbl_score.setText(str(s))

    def set_label(self, name: str):
        self._lbl_name.setText(name)

    def set_tag(self, t: str):
        self._lbl_tag.setText(t)

    def set_active(self, active: bool):
        color = COLOR_PLAYER1 if self.player == PLAYER_1 else COLOR_PLAYER2
        if active:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {COLOR_PANEL};
                    border: 2px solid {color};
                    border-radius: 10px;
                    padding: 6px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {COLOR_PANEL};
                    border: 2px solid {COLOR_BORDER};
                    border-radius: 10px;
                    padding: 6px;
                }}
            """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TicTacToe AI – Minimax + Alpha-Beta")
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(MAIN_STYLE)

        self._config:  Optional[GameConfig]  = None
        self._state:   Optional[GameState]   = None
        self._ai1:     Optional[AIEngine]    = None
        self._ai2:     Optional[AIEngine]    = None
        self._worker:  Optional[AIWorker]    = None
        self._ai_busy  = False
        self._paused   = False
        self._cvc_timer = QTimer(self)
        self._cvc_timer.setSingleShot(True)
        self._cvc_timer.timeout.connect(self._cvc_step)

        self._build_ui()
        self._start_new_game(GameConfig())

    # ── Xây UI ──────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Cột trái: bảng điều khiển ────────────────────────
        left = QWidget()
        left.setFixedWidth(220)
        left.setStyleSheet(f"background:{COLOR_BG2};border-right:1px solid {COLOR_BORDER};")
        llay = QVBoxLayout(left)
        llay.setContentsMargins(14, 20, 14, 20)
        llay.setSpacing(14)

        # Logo
        logo = QLabel("✕ ○")
        logo.setObjectName("title")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        llay.addWidget(logo)
        sub = QLabel("TIC  TAC  TOE")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        llay.addWidget(sub)

        llay.addSpacing(10)

        # Player cards
        cards_lay = QHBoxLayout()
        self._card1 = PlayerCard(PLAYER_1)
        self._card2 = PlayerCard(PLAYER_2)
        cards_lay.addWidget(self._card1)
        cards_lay.addWidget(self._card2)
        llay.addLayout(cards_lay)

        # Match info
        self._lbl_match = QLabel("Hiệp 1 / 1")
        self._lbl_match.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_match.setStyleSheet("color:#8888aa;font-size:11px;")
        llay.addWidget(self._lbl_match)

        llay.addSpacing(6)

        # Nút điều khiển
        self._btn_settings = _btn("⚙  Cài đặt", "btnSettings")
        self._btn_settings.clicked.connect(self._open_settings)
        llay.addWidget(self._btn_settings)

        self._btn_new = _btn("▶  Ván mới", "btnNew")
        self._btn_new.clicked.connect(self._restart_match)
        llay.addWidget(self._btn_new)

        self._btn_next = _btn("⏭  Hiệp tiếp", "btnNext")
        self._btn_next.clicked.connect(self._next_game)
        self._btn_next.setVisible(False)
        llay.addWidget(self._btn_next)

        self._btn_reset = _btn("↺  Hiệp lại", "btnReset")
        self._btn_reset.clicked.connect(self._reset_game)
        llay.addWidget(self._btn_reset)

        # CvC controls
        self._grp_cvc = QGroupBox("Điều khiển Máy vs Máy")
        cvc_lay = QVBoxLayout(self._grp_cvc)
        cvc_lay.setSpacing(6)

        self._btn_pause = _btn("⏸  Tạm dừng", "btnPause")
        self._btn_pause.clicked.connect(self._toggle_pause)
        cvc_lay.addWidget(self._btn_pause)

        self._chk_ai1_on = QCheckBox("🤖 Bật Máy 1 (X)")
        self._chk_ai1_on.setChecked(True)
        self._chk_ai1_on.stateChanged.connect(self._on_cvc_toggle)
        cvc_lay.addWidget(self._chk_ai1_on)

        self._chk_ai2_on = QCheckBox("🤖 Bật Máy 2 (O)")
        self._chk_ai2_on.setChecked(True)
        self._chk_ai2_on.stateChanged.connect(self._on_cvc_toggle)
        cvc_lay.addWidget(self._chk_ai2_on)

        self._grp_cvc.setVisible(False)
        llay.addWidget(self._grp_cvc)

        # AI options
        self._grp_ai_opts = QGroupBox("Hiển thị AI")
        ai_opt_lay = QVBoxLayout(self._grp_ai_opts)
        self._chk_heatmap = QCheckBox("Hiện trọng số heatmap")
        self._chk_heatmap.setChecked(True)
        self._chk_heatmap.stateChanged.connect(self._on_heatmap_toggle)
        ai_opt_lay.addWidget(self._chk_heatmap)
        self._grp_ai_opts.setVisible(False)
        llay.addWidget(self._grp_ai_opts)

        llay.addStretch()

        # Nodes info
        self._lbl_nodes = QLabel("")
        self._lbl_nodes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_nodes.setStyleSheet("color:#555577;font-size:10px;")
        llay.addWidget(self._lbl_nodes)

        root.addWidget(left)

        # ── Cột giữa: bàn cờ ─────────────────────────────────
        mid = QWidget()
        mlay = QVBoxLayout(mid)
        mlay.setContentsMargins(20, 20, 20, 20)
        mlay.setSpacing(12)

        self._lbl_status = QLabel("Chọn cài đặt để bắt đầu")
        self._lbl_status.setObjectName("status")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mlay.addWidget(self._lbl_status, 0, Qt.AlignmentFlag.AlignHCenter)

        self._lbl_thinking = QLabel("")
        self._lbl_thinking.setObjectName("thinking")
        self._lbl_thinking.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mlay.addWidget(self._lbl_thinking, 0, Qt.AlignmentFlag.AlignHCenter)

        self._board_widget = BoardWidget()
        mlay.addWidget(self._board_widget, 1)
        self._board_widget.cell_clicked.connect(self._on_cell_clicked)

        root.addWidget(mid, 1)

    # ── Game lifecycle ───────────────────────────────────────
    def _start_new_game(self, cfg: GameConfig):
        self._config = cfg
        # Huỷ AI cũ
        self._stop_ai()
        self._paused = False
        self._cvc_timer.stop()

        # Tạo AI
        if cfg.mode in (MODE_PVC, MODE_CVC):
            self._ai2 = AIEngine(PLAYER_2, cfg.diff_ai2)
        if cfg.mode == MODE_CVC:
            self._ai1 = AIEngine(PLAYER_1, cfg.diff_ai1)

        # Cập nhật UI
        is_cvc = cfg.mode == MODE_CVC
        is_ai  = cfg.mode in (MODE_PVC, MODE_CVC)
        self._grp_cvc.setVisible(is_cvc)
        self._grp_ai_opts.setVisible(is_ai)

        p1_label = "🤖 Máy 1" if cfg.mode == MODE_CVC else "🧑 Người 1"
        p2_label = "🤖 Máy 2" if cfg.mode in (MODE_PVC, MODE_CVC) else "🧑 Người 2"
        diff1 = f"[{cfg.diff_ai1}]" if cfg.mode == MODE_CVC else ""
        diff2 = f"[{cfg.diff_ai2}]" if cfg.mode in (MODE_PVC, MODE_CVC) else ""
        self._card1.set_label(p1_label)
        self._card1.set_tag(diff1)
        self._card2.set_label(p2_label)
        self._card2.set_tag(diff2)

        self._new_round()

    def _new_round(self):
        self._state  = GameState(self._config)
        self._board_widget.clear_heatmap()
        self._board_widget.set_interactive(True)
        self._btn_next.setVisible(False)
        self._lbl_nodes.setText("")
        self._refresh_display()

        if self._config.mode == MODE_CVC:
            self._schedule_cvc()
        elif self._config.mode == MODE_PVC and \
                self._state.current_player == PLAYER_2:
            self._ai_move()

    def _restart_match(self):
        if self._config:
            self._config.first_player = PLAYER_1
            self._config.wins_needed  = self._config.wins_needed
            self._start_new_game(self._config)

    def _reset_game(self):
        if self._config and self._state:
            self._stop_ai()
            self._cvc_timer.stop()
            self._state._new_game()
            self._board_widget.clear_heatmap()
            self._board_widget.set_interactive(True)
            self._btn_next.setVisible(False)
            self._refresh_display()
            if self._config.mode == MODE_CVC:
                self._schedule_cvc()
            elif self._config.mode == MODE_PVC and \
                    self._state.current_player == PLAYER_2:
                self._ai_move()

    def _next_game(self):
        if self._state and self._state.game_over:
            if self._state.is_match_over:
                self._restart_match()
            else:
                self._state.next_game()
                self._board_widget.clear_heatmap()
                self._board_widget.set_interactive(True)
                self._btn_next.setVisible(False)
                self._refresh_display()
                if self._config.mode == MODE_CVC:
                    self._schedule_cvc()
                elif self._config.mode == MODE_PVC and \
                        self._state.current_player == PLAYER_2:
                    self._ai_move()

    # ── Click ô cờ ──────────────────────────────────────────
    @pyqtSlot(int, int)
    def _on_cell_clicked(self, row: int, col: int):
        if not self._state or self._state.game_over:
            return
        if self._ai_busy:
            return
        if self._config.mode == MODE_CVC:
            return
        if self._config.mode == MODE_PVC and \
                self._state.current_player == PLAYER_2:
            return

        self._board_widget.clear_heatmap()
        if self._state.make_move(row, col):
            self._refresh_display()
            if not self._state.game_over and self._config.mode == MODE_PVC:
                self._ai_move()

    # ── AI Move ─────────────────────────────────────────────
    def _ai_move(self):
        if not self._state or self._state.game_over:
            return
        self._ai_busy = True
        self._board_widget.set_interactive(False)

        player = self._state.current_player
        engine = self._ai1 if (player == PLAYER_1 and self._config.mode == MODE_CVC) \
                 else self._ai2

        if engine is None:
            self._ai_busy = False
            return

        diff_label = engine.difficulty
        sym = PLAYER_SYMBOL[player]
        self._lbl_thinking.setText(f"🤖 {sym} đang tính ({diff_label})…")

        def on_done(move: AIMove):
            # Chạy trên main thread qua QTimer
            self._pending_move = move
            self._pending_engine = engine
            QTimer.singleShot(0, self._apply_ai_move)

        def on_heatmap(hm, pruned):
            if self._chk_heatmap.isChecked():
                self._board_widget.set_heatmap(hm, pruned)

        self._worker = AIWorker(engine, self._state.board,
                                on_done, on_heatmap)
        self._worker.start()

    @pyqtSlot()
    def _apply_ai_move(self):
        move = getattr(self, '_pending_move', None)
        engine = getattr(self, '_pending_engine', None)
        if not move or not self._state:
            self._ai_busy = False
            return

        nodes = engine.nodes_visited if engine else 0
        self._lbl_nodes.setText(f"Nodes: {nodes:,}")
        self._lbl_thinking.setText("")

        if move.row >= 0:
            if self._chk_heatmap.isChecked():
                self._board_widget.set_heatmap(move.heatmap, move.pruned)
            self._state.make_move(move.row, move.col)

        self._ai_busy = False
        self._board_widget.set_interactive(True)
        self._refresh_display()

        if self._state.game_over:
            self._on_game_over()

    def _stop_ai(self):
        if self._worker and self._worker.is_alive():
            if self._ai1: self._ai1.stop()
            if self._ai2: self._ai2.stop()
        self._ai_busy = False
        self._lbl_thinking.setText("")

    # ── CvC ─────────────────────────────────────────────────
    def _schedule_cvc(self):
        if self._paused or self._state.game_over:
            return
        self._cvc_timer.start(CVC_DELAY_MS)

    def _cvc_step(self):
        if not self._state or self._state.game_over or self._paused:
            return

        player = self._state.current_player
        # Kiểm tra máy có bị tắt không
        if player == PLAYER_1 and not self._chk_ai1_on.isChecked():
            return
        if player == PLAYER_2 and not self._chk_ai2_on.isChecked():
            return

        self._ai_move_cvc()

    def _ai_move_cvc(self):
        if not self._state or self._state.game_over:
            return
        self._ai_busy = True

        player = self._state.current_player
        engine = self._ai1 if player == PLAYER_1 else self._ai2
        sym = PLAYER_SYMBOL[player]
        self._lbl_thinking.setText(f"🤖 {sym} đang tính…")

        def on_done(move: AIMove):
            self._pending_move   = move
            self._pending_engine = engine
            QTimer.singleShot(0, self._apply_cvc_move)

        def on_heatmap(hm, pruned):
            if self._chk_heatmap.isChecked():
                self._board_widget.set_heatmap(hm, pruned)

        self._worker = AIWorker(engine, self._state.board,
                                on_done, on_heatmap)
        self._worker.start()

    @pyqtSlot()
    def _apply_cvc_move(self):
        move = getattr(self, '_pending_move', None)
        engine = getattr(self, '_pending_engine', None)
        if not move or not self._state:
            self._ai_busy = False
            return

        nodes = engine.nodes_visited if engine else 0
        self._lbl_nodes.setText(f"Nodes: {nodes:,}")
        self._lbl_thinking.setText("")

        if move.row >= 0:
            if self._chk_heatmap.isChecked():
                self._board_widget.set_heatmap(move.heatmap, move.pruned)
            self._state.make_move(move.row, move.col)

        self._ai_busy = False
        self._refresh_display()

        if self._state.game_over:
            self._on_game_over()
        elif not self._paused:
            self._schedule_cvc()

    def _toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self._btn_pause.setText("▶  Tiếp tục")
            self._cvc_timer.stop()
        else:
            self._btn_pause.setText("⏸  Tạm dừng")
            if self._config.mode == MODE_CVC and not self._state.game_over:
                self._schedule_cvc()

    def _on_cvc_toggle(self):
        if not self._paused and self._config and \
                self._config.mode == MODE_CVC and \
                self._state and not self._state.game_over:
            if not self._cvc_timer.isActive() and not self._ai_busy:
                self._schedule_cvc()

    # ── Game over ───────────────────────────────────────────
    def _on_game_over(self):
        self._board_widget.set_interactive(False)
        is_last = self._state.is_match_over
        self._btn_next.setVisible(True)
        if is_last:
            self._btn_next.setText("▶  Ván mới")
        else:
            self._btn_next.setText("⏭  Hiệp tiếp")

    # ── Refresh UI ──────────────────────────────────────────
    def _refresh_display(self):
        if not self._state:
            return
        st = self._state

        # Bàn cờ
        self._board_widget.set_board(
            st.board.grid, st.board.size,
            st.winning_cells, st.board.last_move,
        )

        # Điểm
        self._card1.set_score(st.score[PLAYER_1])
        self._card2.set_score(st.score[PLAYER_2])
        self._card1.set_active(st.current_player == PLAYER_1 and not st.game_over)
        self._card2.set_active(st.current_player == PLAYER_2 and not st.game_over)

        # Hiệp
        self._lbl_match.setText(
            f"Hiệp {st.current_game}  |  Cần {self._config.wins_needed} hiệp thắng"
        )

        # Status
        if st.game_over:
            if st.is_draw:
                msg = "🤝  Hoà!"
            else:
                sym  = PLAYER_SYMBOL[st.winner]
                name = "Người 1" if st.winner == PLAYER_1 else "Người 2"
                if self._config.mode == MODE_CVC:
                    name = f"Máy {st.winner}"
                elif self._config.mode == MODE_PVC and st.winner == PLAYER_2:
                    name = "Máy"
                msg = f"🏆  {sym} – {name} thắng!"

            match_w = st.match_winner()
            if match_w:
                mname = "Người 1" if match_w == PLAYER_1 else "Người 2"
                if self._config.mode == MODE_CVC:
                    mname = f"Máy {match_w}"
                msg += f"  🎖  {mname} thắng match!"
            self._lbl_status.setText(msg)
        else:
            sym  = PLAYER_SYMBOL[st.current_player]
            p    = st.current_player
            name = f"Người {p}"
            if self._config.mode == MODE_CVC:
                name = f"Máy {p}"
            elif self._config.mode == MODE_PVC and p == PLAYER_2:
                name = "Máy"
            self._lbl_status.setText(f"Lượt {sym} – {name}")

    # ── Settings ────────────────────────────────────────────
    def _open_settings(self):
        dlg = SettingsDialog(self, self._config)
        dlg.config_ready.connect(self._start_new_game)
        dlg.exec()

    def _on_heatmap_toggle(self, state):
        show = bool(state)
        self._board_widget.set_show_heatmap(show)
        if not show:
            self._board_widget.clear_heatmap()

    # ── Overrides ───────────────────────────────────────────
    def closeEvent(self, ev):
        self._stop_ai()
        self._cvc_timer.stop()
        super().closeEvent(ev)
