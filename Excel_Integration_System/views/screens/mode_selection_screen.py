from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QPushButton
)

from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_BORDER, C_TEXT_MUTED, C_CARD,
    _qfont, _styled_btn
)

class ModeSelectionScreen(QWidget):
    """
    Màn hình chọn phương án (Nối dài, Bổ sung, Dọn dẹp).
    Hiển thị ngay sau khi bấm Gộp hồ sơ.
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window
        self.on_mode_selected: Callable[[int], None] = lambda m: None
        self.on_back: Callable[[], None] = lambda: None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(24)

        lbl_title = QLabel("CHỌN PHƯƠNG ÁN GỘP")
        lbl_title.setFont(_qfont("Segoe UI", 20, bold=True))
        lbl_title.setStyleSheet(f"color: {C_PRIMARY};")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_sub = QLabel("Bạn muốn xử lý dữ liệu từ các file này như thế nào?")
        lbl_sub.setFont(_qfont("Segoe UI", 12))
        lbl_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root.addWidget(lbl_title)
        root.addWidget(lbl_sub)
        root.addSpacing(20)

        # Mode Cards
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(32)
        cards_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card 1: Nối dài
        card_append = self._make_card(
            "📋 Nối Dài Danh Sách",
            "Chồng các danh sách lên nhau để tạo thành một bảng dữ liệu dài hơn.\n\n"
            "• Thích hợp cho: Gộp báo cáo tháng, nối nhiều danh sách khách hàng.\n",
            C_PRIMARY,
            lambda: self.on_mode_selected(1)
        )
        cards_lay.addWidget(card_append)

        # Card 2: Bổ sung thông tin
        card_supplement = self._make_card(
            "🔗 Bổ Sung Thông Tin",
            "Lấy File #1 làm gốc. Dò tìm và đắp thêm cột dữ liệu từ các file phụ sang file gốc dựa trên chìa khóa (VD: Số CCCD).\n\n"
            "• Thích hợp cho: Làm giàu dữ liệu, nối thêm cột.",
            C_ACCENT,
            lambda: self.on_mode_selected(2)
        )
        cards_lay.addWidget(card_supplement)
        
        # Card 3: Chuẩn hóa 1 file
        card_clean = self._make_card(
            "✨ Dọn Dẹp & Chuẩn Hóa",
            "Quy hoạch lại cấu trúc của 1 file duy nhất. Gom các cột đánh dấu (X) thành các khối liền mạch hoặc gộp thành 1 cột phân loại.\n\n"
            "• Thích hợp cho: Dọn dẹp file lộn xộn, làm gọn bảng dữ liệu.",
            "#2E7D32", # Green
            lambda: self.on_mode_selected(3)
        )
        cards_lay.addWidget(card_clean)

        root.addLayout(cards_lay)
        root.addStretch()

        # Bottom nav
        nav = QHBoxLayout()
        self.btn_back = _styled_btn("◀  Quay lại trang chủ", bg="#546E7A", hover_bg="#37474F", width=200, height=40)
        self.btn_back.clicked.connect(lambda: self.on_back())
        nav.addWidget(self.btn_back)
        nav.addStretch()

        root.addLayout(nav)

    def _make_card(self, title: str, desc: str, color: str, callback: Callable[[], None]) -> QFrame:
        card = QFrame()
        card.setFixedSize(360, 220)
        card.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 2px solid {color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background: #F8FAFC;
                border: 2px solid {color};
            }}
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        lbl_t = QLabel(title)
        lbl_t.setFont(_qfont("Segoe UI", 16, bold=True))
        lbl_t.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_d = QLabel(desc)
        lbl_d.setFont(_qfont("Segoe UI", 11))
        lbl_d.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none; background: transparent;")
        lbl_d.setWordWrap(True)
        lbl_d.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        lay.addWidget(lbl_t)
        lay.addWidget(lbl_d, stretch=1)

        # Make entire card clickable
        card.mousePressEvent = lambda e: callback()
        lbl_t.mousePressEvent = lambda e: callback()
        lbl_d.mousePressEvent = lambda e: callback()

        return card
