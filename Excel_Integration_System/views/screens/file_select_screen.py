"""
views/screens/file_select_screen.py
=====================================
FileSelectScreen – Màn hình chọn file Excel (không phân biệt gốc/phụ).

Xuất hiện sau khi người dùng nhấn "Bắt đầu" ở HomeScreen.
Cho phép chọn nhiều file Excel, xem danh sách, rồi tiếp tục xử lý.

DTO Getters:
    get_selected_files() → List[str]
"""

from __future__ import annotations

import os
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_SUCCESS, C_BORDER,
    C_TEXT_MUTED, C_CARD, C_SIDEBAR_ACT,
    _qfont, _styled_btn,
)


class FileSelectScreen(QWidget):
    """
    Màn hình chọn file Excel để tiếp tục gộp hồ sơ.

    Sau khi khởi tạo, Controller gán:
        screen.btn_browse.clicked.connect(controller.handle_browse_files)
        screen.btn_proceed.clicked.connect(lambda: controller.handle_proceed_to_structure(screen))
        screen.btn_back.clicked.connect(app_controller.show_home)
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window
        self._selected_files: List[str] = []
        self._build_ui()

    # ==================================================================
    # BUILD UI
    # ==================================================================
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        root = QVBoxLayout(scroll_content)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # ── Header ──────────────────────────────────────────────────────
        lbl_title = QLabel("📁  Chọn file Excel cần xử lý")
        lbl_title.setFont(_qfont("Segoe UI", 20, bold=True))
        lbl_title.setStyleSheet(f"color: {C_PRIMARY};")
        root.addWidget(lbl_title)

        lbl_sub = QLabel("Chọn một hoặc nhiều file Excel. Hệ thống sẽ hướng dẫn bạn thiết lập cấu trúc và phương án gộp ở các bước tiếp theo.")
        lbl_sub.setFont(_qfont("Segoe UI", 12))
        lbl_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")
        lbl_sub.setWordWrap(True)
        root.addWidget(lbl_sub)

        # ── Card upload ──────────────────────────────────────────────────
        upload_card = QFrame()
        upload_card.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 1px solid {C_BORDER};
                border-radius: 12px;
            }}
        """)

        card_layout = QVBoxLayout(upload_card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(12)

        # Trạng thái file đã chọn
        self._lbl_file_count = QLabel("Chưa có tệp tin nào được chọn  •  Hỗ trợ .xlsx, .xls")
        self._lbl_file_count.setFont(_qfont("Segoe UI", 12))
        self._lbl_file_count.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none;")
        card_layout.addWidget(self._lbl_file_count)

        # Nút Duyệt file
        self.btn_browse = _styled_btn(
            "📂  Duyệt file…",
            bg="#EEF2FF", fg=C_PRIMARY, hover_bg=C_BORDER,
            width=160, height=40, border=C_BORDER,
        )
        card_layout.addWidget(self.btn_browse, alignment=Qt.AlignmentFlag.AlignLeft)

        # Danh sách file đã chọn
        self._file_list_widget = QListWidget()
        self._file_list_widget.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {C_BORDER};
                border-radius: 8px;
                background: {C_CARD};
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {C_BORDER};
            }}
            QListWidget::item:selected {{
                background: #DBEAFE;
                color: {C_PRIMARY};
            }}
            QListWidget::item:hover {{
                background: #F0F4FF;
            }}
        """)
        self._file_list_widget.setVisible(False)
        self._file_list_widget.setMinimumHeight(80)
        self._file_list_widget.setMaximumHeight(240)
        card_layout.addWidget(self._file_list_widget)

        # Nút xoá file đã chọn
        self._btn_clear = _styled_btn(
            "🗑  Xoá danh sách",
            bg="#FEF2F2", fg="#DC2626", hover_bg="#FECACA",
            width=150, height=32, border="#FECACA",
        )
        self._btn_clear.setVisible(False)
        self._btn_clear.clicked.connect(self._clear_files)
        card_layout.addWidget(self._btn_clear, alignment=Qt.AlignmentFlag.AlignLeft)

        root.addWidget(upload_card)

        # ── Nút Tiếp tục ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_back = _styled_btn(
            "◀  Quay lại",
            bg="#546E7A", hover_bg="#37474F",
            width=140, height=42, bold=False,
        )

        self.btn_proceed = _styled_btn(
            "Tiếp tục  ➔",
            bg=C_PRIMARY, hover_bg=C_SIDEBAR_ACT,
            width=200, height=42, bold=True, font_size=13,
        )

        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_proceed)
        btn_row.addStretch()
        root.addLayout(btn_row)

        root.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    # ==================================================================
    # PRIVATE HELPERS
    # ==================================================================
    def _clear_files(self) -> None:
        """Xoá toàn bộ danh sách file đã chọn."""
        self._selected_files.clear()
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        """Cập nhật giao diện theo danh sách file hiện tại."""
        count = len(self._selected_files)

        if count == 0:
            self._lbl_file_count.setText("Chưa có tệp tin nào được chọn  •  Hỗ trợ .xlsx, .xls")
            self._lbl_file_count.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none;")
            self._file_list_widget.setVisible(False)
            self._btn_clear.setVisible(False)
        else:
            self._lbl_file_count.setText(f"✅  Đã chọn {count} file")
            self._lbl_file_count.setStyleSheet(f"color: {C_SUCCESS}; border: none;")
            self._file_list_widget.setVisible(True)
            self._btn_clear.setVisible(True)

            self._file_list_widget.clear()
            for i, fp in enumerate(self._selected_files):
                item = QListWidgetItem(f"  {i + 1}.  📄  {os.path.basename(fp)}")
                self._file_list_widget.addItem(item)

    # ==================================================================
    # PUBLIC API
    # ==================================================================
    def set_selected_files(self, files: List[str]) -> None:
        """Controller gọi để cập nhật danh sách file."""
        self._selected_files = list(files)
        self._refresh_ui()

    def get_selected_files(self) -> List[str]:
        """DTO Getter: trả về danh sách file đã chọn."""
        return list(self._selected_files)

    def get_merge_mode(self) -> int:
        """Trả về chế độ gộp mặc định (mode thực sự chọn ở ModeSelectionScreen)."""
        return 1
