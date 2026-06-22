"""
views/screens/source_file_select_screen.py
==========================================
SourceFileSelectScreen – Màn hình chỉ định file gốc và file phụ.

Chỉ xuất hiện khi người dùng chọn chế độ "Bổ sung Thông Tin" (mode 2).
Cho phép người dùng chỉ định rõ file nào là File Gốc và file nào là File Phụ.

DTO Getters:
    get_master_file()   → str       (đường dẫn file gốc)
    get_aux_files()     → List[str] (danh sách file phụ)
    get_ordered_files() → List[str] (file gốc ở đầu, rồi đến file phụ)
"""

from __future__ import annotations

import os
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_SUCCESS, C_DANGER, C_BORDER,
    C_TEXT_MUTED, C_CARD, C_SIDEBAR_ACT, C_WARN,
    _qfont, _styled_btn,
)


class SourceFileSelectScreen(QWidget):
    """
    Màn hình chỉ định File Gốc / File Phụ cho chế độ "Bổ sung Thông Tin".

    Sau khi khởi tạo, Controller gán:
        screen.btn_confirm.clicked.connect(lambda: controller.handle_confirm_source_files(screen))
        screen.btn_back.clicked.connect(app_controller.show_mode_selection)
    """

    def __init__(self, window: MainWindow, files: List[str]) -> None:
        super().__init__()
        self._window = window
        self._files: List[str] = list(files)  # Tất cả file đã chọn
        self._master_file: Optional[str] = files[0] if files else None
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
        lbl_title = QLabel("🔗  Chỉ định File Gốc & File Phụ")
        lbl_title.setFont(_qfont("Segoe UI", 20, bold=True))
        lbl_title.setStyleSheet(f"color: {C_PRIMARY};")
        root.addWidget(lbl_title)

        lbl_sub = QLabel(
            "Chế độ Bổ Sung Thông Tin cần biết file nào là Gốc (nguồn dữ liệu chính) "
            "và file nào là Phụ (nguồn bổ sung). Hệ thống sẽ dò tìm và đắp thêm cột "
            "từ file phụ sang file gốc dựa trên chìa khóa chung."
        )
        lbl_sub.setFont(_qfont("Segoe UI", 12))
        lbl_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")
        lbl_sub.setWordWrap(True)
        root.addWidget(lbl_sub)

        # ── Card chọn File Gốc ─────────────────────────────────────────
        master_card = QFrame()
        master_card.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 2px solid {C_PRIMARY};
                border-radius: 12px;
            }}
        """)

        master_layout = QVBoxLayout(master_card)
        master_layout.setContentsMargins(24, 18, 24, 18)
        master_layout.setSpacing(10)

        master_header = QHBoxLayout()
        lbl_master_icon = QLabel("📌")
        lbl_master_icon.setFont(QFont("Segoe UI", 18))
        lbl_master_icon.setStyleSheet("border: none; background: transparent;")

        lbl_master_title = QLabel("File Gốc")
        lbl_master_title.setFont(_qfont("Segoe UI", 15, bold=True))
        lbl_master_title.setStyleSheet(f"color: {C_PRIMARY}; border: none; background: transparent;")

        lbl_master_badge = QLabel("  Nguồn dữ liệu chính  ")
        lbl_master_badge.setFont(_qfont("Segoe UI", 10))
        lbl_master_badge.setStyleSheet(f"""
            color: white;
            background: {C_PRIMARY};
            border-radius: 6px;
            padding: 2px 6px;
            border: none;
        """)

        master_header.addWidget(lbl_master_icon)
        master_header.addWidget(lbl_master_title)
        master_header.addWidget(lbl_master_badge)
        master_header.addStretch()
        master_layout.addLayout(master_header)

        lbl_master_desc = QLabel("Chọn file sẽ được dùng làm danh sách gốc. Dữ liệu từ file phụ sẽ được ghép sang file này.")
        lbl_master_desc.setFont(_qfont("Segoe UI", 11))
        lbl_master_desc.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none; background: transparent;")
        lbl_master_desc.setWordWrap(True)
        master_layout.addWidget(lbl_master_desc)

        # Dropdown chọn file gốc
        self._combo_master = QComboBox()
        self._combo_master.setFont(_qfont("Segoe UI", 12))
        self._combo_master.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {C_PRIMARY};
                border-radius: 6px;
                padding: 6px 10px;
                background: white;
                color: #1a1a2e;
                min-height: 36px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {C_BORDER};
                selection-background-color: #DBEAFE;
                selection-color: {C_PRIMARY};
            }}
        """)
        for fp in self._files:
            self._combo_master.addItem(f"📄  {os.path.basename(fp)}", fp)
        self._combo_master.currentIndexChanged.connect(self._on_master_changed)
        master_layout.addWidget(self._combo_master)

        root.addWidget(master_card)

        # ── Card File Phụ (danh sách còn lại) ─────────────────────────
        aux_card = QFrame()
        aux_card.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 2px solid {C_ACCENT};
                border-radius: 12px;
            }}
        """)

        aux_layout = QVBoxLayout(aux_card)
        aux_layout.setContentsMargins(24, 18, 24, 18)
        aux_layout.setSpacing(10)

        aux_header = QHBoxLayout()
        lbl_aux_icon = QLabel("📎")
        lbl_aux_icon.setFont(QFont("Segoe UI", 18))
        lbl_aux_icon.setStyleSheet("border: none; background: transparent;")

        lbl_aux_title = QLabel("File Phụ")
        lbl_aux_title.setFont(_qfont("Segoe UI", 15, bold=True))
        lbl_aux_title.setStyleSheet(f"color: {C_ACCENT}; border: none; background: transparent;")

        lbl_aux_badge = QLabel("  Nguồn bổ sung  ")
        lbl_aux_badge.setFont(_qfont("Segoe UI", 10))
        lbl_aux_badge.setStyleSheet(f"""
            color: white;
            background: {C_ACCENT};
            border-radius: 6px;
            padding: 2px 6px;
            border: none;
        """)

        aux_header.addWidget(lbl_aux_icon)
        aux_header.addWidget(lbl_aux_title)
        aux_header.addWidget(lbl_aux_badge)
        aux_header.addStretch()
        aux_layout.addLayout(aux_header)

        lbl_aux_desc = QLabel("Các file còn lại sẽ là File Phụ — dữ liệu từ đây sẽ được ghép sang File Gốc theo chìa khóa chung.")
        lbl_aux_desc.setFont(_qfont("Segoe UI", 11))
        lbl_aux_desc.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none; background: transparent;")
        lbl_aux_desc.setWordWrap(True)
        aux_layout.addWidget(lbl_aux_desc)

        self._aux_list = QListWidget()
        self._aux_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {C_ACCENT};
                border-radius: 8px;
                background: white;
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {C_BORDER};
            }}
        """)
        self._aux_list.setMinimumHeight(80)
        self._aux_list.setMaximumHeight(200)
        aux_layout.addWidget(self._aux_list)

        root.addWidget(aux_card)

        # ── Tóm tắt cấu hình ──────────────────────────────────────────
        self._lbl_summary = QLabel()
        self._lbl_summary.setFont(_qfont("Segoe UI", 11))
        self._lbl_summary.setStyleSheet(f"""
            color: {C_TEXT_MUTED};
            background: #F8FAFC;
            border: 1px solid {C_BORDER};
            border-radius: 8px;
            padding: 10px 14px;
        """)
        self._lbl_summary.setWordWrap(True)
        root.addWidget(self._lbl_summary)

        # ── Nút điều hướng ────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_back = _styled_btn(
            "◀  Quay lại chọn chế độ",
            bg="#546E7A", hover_bg="#37474F",
            width=200, height=42,
        )

        self.btn_confirm = _styled_btn(
            "✅  Xác nhận & Tiếp tục  ➔",
            bg=C_PRIMARY, hover_bg=C_SIDEBAR_ACT,
            width=230, height=42, bold=True, font_size=13,
        )

        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_confirm)
        btn_row.addStretch()
        root.addLayout(btn_row)

        root.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Cập nhật danh sách file phụ lần đầu
        self._update_aux_list()
        self._update_summary()

    # ==================================================================
    # PRIVATE HELPERS
    # ==================================================================
    def _on_master_changed(self, index: int) -> None:
        """Khi người dùng đổi file gốc → cập nhật danh sách file phụ."""
        if index >= 0:
            self._master_file = self._combo_master.itemData(index)
        self._update_aux_list()
        self._update_summary()

    def _update_aux_list(self) -> None:
        """Cập nhật danh sách file phụ = tất cả file trừ file gốc."""
        self._aux_list.clear()
        for fp in self._files:
            if fp != self._master_file:
                item = QListWidgetItem(f"  📄  {os.path.basename(fp)}")
                self._aux_list.addItem(item)

    def _update_summary(self) -> None:
        """Cập nhật dòng tóm tắt cấu hình."""
        aux_count = len(self._files) - 1
        master_name = os.path.basename(self._master_file) if self._master_file else "?"
        self._lbl_summary.setText(
            f"ℹ️  Cấu hình: File Gốc = \"{master_name}\"  •  {aux_count} file phụ sẽ được ghép sang."
        )

    # ==================================================================
    # PUBLIC DTO GETTERS
    # ==================================================================
    def get_master_file(self) -> Optional[str]:
        """Trả về đường dẫn File Gốc được chọn."""
        return self._master_file

    def get_aux_files(self) -> List[str]:
        """Trả về danh sách File Phụ (tất cả file trừ file gốc)."""
        return [fp for fp in self._files if fp != self._master_file]

    def get_ordered_files(self) -> List[str]:
        """Trả về danh sách file theo thứ tự: File Gốc đầu tiên, rồi đến File Phụ."""
        result = []
        if self._master_file:
            result.append(self._master_file)
        result.extend(self.get_aux_files())
        return result
