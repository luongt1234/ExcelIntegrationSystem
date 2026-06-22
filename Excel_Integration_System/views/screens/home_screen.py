"""
views/screens/home_screen.py
============================
HomeScreen – Màn hình trang chủ chọn chế độ.

Passive View: chỉ render widgets và cung cấp DTO Getter.
Controller gán lệnh cho các nút sau khi khởi tạo.

Không còn upload file ở màn hình chính.
Việc chọn file được thực hiện ở FileSelectScreen sau khi nhấn "Bắt đầu".
"""

from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_BORDER,
    C_TEXT_MUTED, C_CARD,
    C_SIDEBAR_ACT,
    _qfont, _styled_btn,
)


class HomeScreen(QWidget):
    """
    Màn hình trang chủ.

    Sau khi khởi tạo, Controller gán:
        screen.btn_person.clicked.connect(controller.show_file_select_screen)
        screen.btn_goods.clicked.connect(controller.show_goods_start)
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window

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
        root.setContentsMargins(28, 18, 28, 18)
        root.setSpacing(16)

        # ── Header section ─────────────────────────────────────────────
        self._build_header_section(root)

        # ── 2 card chế độ ──────────────────────────────────────────────
        self._build_mode_cards(root)

        root.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _build_header_section(self, layout: QVBoxLayout) -> None:
        self._lbl_title = QLabel(
            self._window.get_ui_customization("welcome_title", "Chào mừng đến DataMerge Pro")
        )
        self._lbl_title.setFont(_qfont("Segoe UI", 20, bold=True))
        self._lbl_title.setStyleSheet(f"color: {C_PRIMARY};")

        self._lbl_sub = QLabel(
            self._window.get_ui_customization(
                "welcome_subtitle",
                "Hợp nhất & chuẩn hóa dữ liệu Excel nhanh chóng, chính xác và bảo mật tuyệt đối.",
            )
        )
        self._lbl_sub.setFont(_qfont("Segoe UI", 12))
        self._lbl_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")

        layout.addWidget(self._lbl_title)
        layout.addWidget(self._lbl_sub)

    def _build_mode_cards(self, layout: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(24)

        # ── Card 1: Gộp hồ sơ người ─────────────────────────────────
        card_person = self._make_mode_card(
            icon="👤",
            title=self._window.get_ui_customization("card_person_title", "Gộp hồ sơ người"),
            subtitle=self._window.get_ui_customization("card_person_subtitle", "Khử trùng & hợp nhất hồ sơ nhân sự"),
            btn_text="Bắt đầu  →",
            btn_bg=C_PRIMARY,
            btn_hover=C_SIDEBAR_ACT,
        )
        self.btn_person = card_person.findChild(QPushButton)
        # Lưu tham chiếu label để reload_ui_text() có thể cập nhật
        labels_person = card_person.findChildren(QLabel)
        self._lbl_card_person_title    = labels_person[1] if len(labels_person) > 1 else None
        self._lbl_card_person_subtitle = labels_person[2] if len(labels_person) > 2 else None
        row.addWidget(card_person)

        # ── Card 2: Gộp hàng hóa ────────────────────────────────────
        card_goods = self._make_mode_card(
            icon="📦",
            title=self._window.get_ui_customization("card_goods_title", "Gộp hàng hóa thông minh"),
            subtitle=self._window.get_ui_customization("card_goods_subtitle", "Chuẩn hóa tên sản phẩm bằng AI"),
            btn_text="Bắt đầu  →",
            btn_bg=C_ACCENT,
            btn_hover="#BF360C",
        )
        self.btn_goods = card_goods.findChild(QPushButton)
        # Lưu tham chiếu label để reload_ui_text() có thể cập nhật
        labels_goods = card_goods.findChildren(QLabel)
        self._lbl_card_goods_title    = labels_goods[1] if len(labels_goods) > 1 else None
        self._lbl_card_goods_subtitle = labels_goods[2] if len(labels_goods) > 2 else None
        row.addWidget(card_goods)

        row.addStretch()
        layout.addLayout(row)

    def _make_mode_card(
        self,
        icon: str,
        title: str,
        subtitle: str,
        btn_text: str,
        btn_bg: str,
        btn_hover: str,
    ) -> QFrame:
        card = QFrame()
        card.setFixedSize(320, 200)
        card.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 1px solid {C_BORDER};
                border-radius: 12px;
            }}
        """)
        vl = QVBoxLayout(card)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.setSpacing(6)

        lbl_icon = QLabel(icon)
        lbl_icon.setFont(QFont("Segoe UI", 32))
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("border: none;")

        lbl_title = QLabel(title)
        lbl_title.setFont(_qfont("Segoe UI", 14, bold=True))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"color: {C_PRIMARY}; border: none;")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setFont(_qfont("Segoe UI", 11))
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none;")

        btn = _styled_btn(
            btn_text, bg=btn_bg, hover_bg=btn_hover,
            width=180, height=36, bold=True, font_size=12,
        )

        vl.addWidget(lbl_icon)
        vl.addWidget(lbl_title)
        vl.addWidget(lbl_sub)
        vl.addSpacing(4)
        vl.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return card



    # ==================================================================
    # PUBLIC: placeholder để tương thích ngược (nếu có code cũ gọi)
    # ==================================================================
    def show_person_flow(self) -> None:
        """Deprecated: không còn khu vực upload ở trang chủ."""
        pass

    def reload_ui_text(self) -> None:
        """Cập nhật lại các QLabel tiêu đề / phụ đề từ settings sau khi UI Editor lưu."""
        self._lbl_title.setText(
            self._window.get_ui_customization("welcome_title", "Chào mừng đến DataMerge Pro")
        )
        self._lbl_sub.setText(
            self._window.get_ui_customization(
                "welcome_subtitle",
                "Hợp nhất & chuẩn hóa dữ liệu Excel nhanh chóng, chính xác và bảo mật tuyệt đối.",
            )
        )
        if self._lbl_card_person_title:
            self._lbl_card_person_title.setText(
                self._window.get_ui_customization("card_person_title", "Gộp hồ sơ người")
            )
        if self._lbl_card_person_subtitle:
            self._lbl_card_person_subtitle.setText(
                self._window.get_ui_customization("card_person_subtitle", "Khử trùng & hợp nhất hồ sơ nhân sự")
            )
        if self._lbl_card_goods_title:
            self._lbl_card_goods_title.setText(
                self._window.get_ui_customization("card_goods_title", "Gộp hàng hóa thông minh")
            )
        if self._lbl_card_goods_subtitle:
            self._lbl_card_goods_subtitle.setText(
                self._window.get_ui_customization("card_goods_subtitle", "Chuẩn hóa tên sản phẩm bằng AI")
            )
