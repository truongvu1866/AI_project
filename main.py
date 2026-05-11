#!/usr/bin/env python3
# ============================================================
#  main.py – Điểm khởi động ứng dụng TicTacToe AI
# ============================================================
import sys
import os

# Thêm thư mục hiện tại vào path để import nội bộ
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

from ui_main import MainWindow
from constants import COLOR_BG


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TicTacToe AI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("TicTacToe")

    # Style tối
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,       QColor(COLOR_BG))
    palette.setColor(QPalette.ColorRole.WindowText,   QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Base,         QColor("#16162a"))
    palette.setColor(QPalette.ColorRole.AlternateBase,QColor("#1e1e35"))
    palette.setColor(QPalette.ColorRole.ToolTipBase,  QColor("#1e1e35"))
    palette.setColor(QPalette.ColorRole.ToolTipText,  QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Text,         QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Button,       QColor("#1e1e35"))
    palette.setColor(QPalette.ColorRole.ButtonText,   QColor("#e0e0f0"))
    palette.setColor(QPalette.ColorRole.Highlight,    QColor("#7c5cfc"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    win.raise_()
    win.activateWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
