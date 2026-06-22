"""
views/main_window.py
====================
MainWindow – QMainWindow root window (thay thế CustomTkinter CTk).

Chỉ chứa:
  • Bố cục tổng thể: Header / Toolbar / QStackedWidget / StatusBar.
  • Helper tạo widget tái dụng (make_card, make_primary_btn, …).
  • Hàm PUBLIC cập nhật UI (update_status, set_header_mode, …).
  • Theme (settings.json), shortcuts (QShortcut).
  • QStackedWidget để AppController swap màn hình (switch thẳng, không animation).

TUYỆT ĐỐI KHÔNG:
  • Import / gọi controller.
  • Chứa logic xử lý dữ liệu.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QPalette,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

# ── Hằng màu & kích thước UI (dùng chung toàn dự án) ────────────────
C_PRIMARY      = "#1B3A6B"
C_ACCENT       = "#E65100"
C_SUCCESS      = "#2E7D32"
C_DANGER       = "#C62828"
C_WARN         = "#F57F17"
C_BG_LIGHT     = "#F5F7FA"
C_CARD         = "#FFFFFF"
C_BORDER       = "#DDE3EE"
C_TEXT_MUTED   = "#7B8CAA"
C_SIDEBAR      = "#1B3A6B"
C_SIDEBAR_ACT  = "#2A5298"
C_TOOLBAR      = "#2a2d2e"
C_STATUSBAR    = "#1f2428"

FONT_TITLE   = ("Segoe UI", 20, True)
FONT_HEADING = ("Segoe UI", 14, True)
FONT_BODY    = ("Segoe UI", 12, False)
FONT_SMALL   = ("Segoe UI", 11, False)
FONT_MONO    = ("Consolas", 11, False)


def _qfont(family: str, size: int, bold: bool = False) -> QFont:
    """Helper tạo QFont nhanh."""
    f = QFont(family, size)
    f.setBold(bold)
    return f


def _styled_btn(
    text: str,
    bg: str,
    fg: str = "#FFFFFF",
    hover_bg: str | None = None,
    width: int | None = None,
    height: int = 36,
    font_size: int = 12,
    bold: bool = False,
    border: str | None = None,
    radius: int = 8,
) -> QPushButton:
    """
    Factory tạo QPushButton với stylesheet inline.
    Tránh lặp code CSS ở nhiều nơi.
    """
    btn = QPushButton(text)
    if width:
        btn.setFixedWidth(width)
    btn.setFixedHeight(height)
    btn.setFont(_qfont("Segoe UI", font_size, bold))
    hover_bg = hover_bg or bg
    border_css = f"border: 1px solid {border};" if border else "border: none;"
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            {border_css}
            border-radius: {radius}px;
            padding: 0 12px;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
        }}
        QPushButton:disabled {{
            background-color: #B0BEC5;
            color: #FFFFFF;
        }}
    """)
    return btn


def _section_label(text: str, color: str = C_PRIMARY, size: int = 16) -> QLabel:
    """Helper tạo QLabel tiêu đề section (dùng chung toàn dự án)."""
    lbl = QLabel(text)
    lbl.setFont(_qfont("Segoe UI", size, bold=True))
    lbl.setStyleSheet(f"color: {color};")
    return lbl


def _sub_label(text: str, color: str = C_TEXT_MUTED, size: int = 12) -> QLabel:
    """Helper tạo QLabel phụ đề section (dùng chung toàn dự án)."""
    lbl = QLabel(text)
    lbl.setFont(_qfont("Segoe UI", size))
    lbl.setStyleSheet(f"color: {color};")
    lbl.setWordWrap(True)
    return lbl


class MainWindow(QMainWindow):
    """
    Cửa sổ chính của ứng dụng (View thuần túy).

    Controller truy cập qua:
        window.stack         – QStackedWidget để show màn hình
        window.btn_export    – QPushButton Export
        window.btn_help      – QPushButton Help
        window.btn_theme     – QPushButton Theme
        window.update_status(message, progress)
        window.set_header_mode(text)
        window.set_export_enabled(enabled)
    """

    _SETTINGS_FILE = "settings.json"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Hệ Thống Tích Hợp Dữ Liệu Excel – v5.0 (PyQt6 MVC)")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 640)

        # ── Settings ─────────────────────────────────────────────────
        self._settings_path = Path(__file__).parent.parent / self._SETTINGS_FILE
        self._ui_settings: dict = {}
        self._load_settings()

        # ── Áp dụng stylesheet toàn cục ──────────────────────────────
        self._apply_global_style()

        # ── Build layout ─────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._build_header(root_layout)
        self._build_toolbar(root_layout)
        self._build_stack(root_layout)
        self._build_statusbar()

    # ==================================================================
    # GLOBAL STYLESHEET
    # ==================================================================
    def _apply_global_style(self) -> None:
        """Áp stylesheet cho toàn bộ ứng dụng."""
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {C_BG_LIGHT};
                font-family: "Segoe UI";
            }}
            QLabel {{
                color: #1A202C;
            }}
            QScrollBar:vertical {{
                background: #F0F0F0;
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #B0BEC5;
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #90A4AE;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: #F0F0F0;
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: #B0BEC5;
                border-radius: 5px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: #90A4AE;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            QTableView {{
                background-color: #FFFFFF;
                alternate-background-color: {C_BG_LIGHT};
                gridline-color: {C_BORDER};
                selection-background-color: #DBEAFE;
                selection-color: {C_PRIMARY};
                border: 1px solid {C_BORDER};
                border-radius: 0px;
                font-size: 11px;
            }}
            QHeaderView::section {{
                background-color: {C_PRIMARY};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 8px;
                border: none;
                border-right: 1px solid {C_SIDEBAR_ACT};
            }}
            QHeaderView::section:hover {{
                background-color: {C_SIDEBAR_ACT};
            }}
            QTabWidget::pane {{
                border: 1px solid {C_BORDER};
                background: #FFFFFF;
            }}
            QTabBar::tab {{
                background: #E2E8F4;
                color: {C_PRIMARY};
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
                border: none;
            }}
            QTabBar::tab:selected {{
                background: {C_PRIMARY};
                color: #FFFFFF;
            }}
            QTabBar::tab:hover:!selected {{
                background: #C5CEDF;
            }}
            QComboBox {{
                border: 1px solid {C_BORDER};
                border-radius: 6px;
                padding: 4px 8px;
                background: #FFFFFF;
                color: #1A202C;
                font-size: 11px;
            }}
            QComboBox:focus {{
                border-color: {C_PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QLineEdit {{
                border: 1px solid {C_BORDER};
                border-radius: 6px;
                padding: 4px 8px;
                background: #FFFFFF;
                color: #1A202C;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {C_PRIMARY};
            }}
            QCheckBox {{
                spacing: 6px;
                font-size: 12px;
                color: #1A202C;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {C_BORDER};
                border-radius: 3px;
                background: #FFFFFF;
            }}
            QCheckBox::indicator:checked {{
                background-color: {C_PRIMARY};
                border-color: {C_PRIMARY};
                image: none;
            }}
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: #37474F;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background: {C_ACCENT};
                border-radius: 4px;
            }}
        """)

    # ==================================================================
    # HEADER
    # ==================================================================
    def _build_header(self, layout: QVBoxLayout) -> None:
        hdr = QFrame()
        hdr.setFixedHeight(56)
        hdr.setStyleSheet(f"background-color: {C_PRIMARY};")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(20, 0, 20, 0)

        # Logo + tên app
        lbl_logo = QLabel("⚡ DataMerge Pro")
        lbl_logo.setFont(_qfont("Segoe UI", 16, bold=True))
        lbl_logo.setStyleSheet("color: #FFFFFF;")

        # Tên màn hình hiện tại
        self._lbl_header_mode = QLabel("Trang chủ")
        self._lbl_header_mode.setFont(_qfont("Segoe UI", 12))
        self._lbl_header_mode.setStyleSheet("color: #93B4E0;")

        # Offline badge
        lbl_offline = QLabel("🔒  100% Offline")
        lbl_offline.setFont(_qfont("Segoe UI", 11))
        lbl_offline.setStyleSheet("color: #64B5F6;")

        hdr_layout.addWidget(lbl_logo)
        hdr_layout.addSpacing(16)
        hdr_layout.addWidget(self._lbl_header_mode)
        hdr_layout.addStretch()
        hdr_layout.addWidget(lbl_offline)

        layout.addWidget(hdr)

    # ==================================================================
    # TOOLBAR
    # ==================================================================
    def _build_toolbar(self, layout: QVBoxLayout) -> None:
        toolbar_frame = QFrame()
        toolbar_frame.setFixedHeight(48)
        toolbar_frame.setStyleSheet(f"background-color: {C_TOOLBAR};")
        tb_layout = QHBoxLayout(toolbar_frame)
        tb_layout.setContentsMargins(12, 6, 12, 6)
        tb_layout.setSpacing(6)

        def _tb_btn(text: str, tooltip: str) -> QPushButton:
            btn = QPushButton(text)
            btn.setFixedSize(QSize(120, 34))
            btn.setFont(_qfont("Segoe UI", 11))
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3d3e;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    background-color: #4a4d4e;
                }
                QPushButton:disabled {
                    background-color: #2a2d2e;
                    color: #666;
                }
            """)
            return btn

        # Controller sẽ connect signal sau
        self.btn_export = _tb_btn("📤  Export", "Xuất file Excel  (Ctrl+E)")
        tb_layout.addWidget(self.btn_export)
        tb_layout.addStretch()
        self.btn_help  = _tb_btn("❓  Help",  "Hướng dẫn nhanh  (F1)")
        self.btn_theme = _tb_btn("🌓  Theme", "Đổi chế độ sáng/tối")
        tb_layout.addWidget(self.btn_help)
        tb_layout.addWidget(self.btn_theme)


        layout.addWidget(toolbar_frame)

    # ==================================================================
    # SCREEN STACK (QStackedWidget)
    # ==================================================================
    def _build_stack(self, layout: QVBoxLayout) -> None:
        """
        QStackedWidget là container cho tất cả màn hình.
        AppController gọi stack.setCurrentWidget(screen) để chuyển màn hình.
        Không destroy widget cũ → chuyển nhanh, không re-create.
        """
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {C_BG_LIGHT};")
        layout.addWidget(self.stack, stretch=1)

    # ==================================================================
    # STATUS BAR
    # ==================================================================
    def _build_statusbar(self) -> None:
        sb = self.statusBar()
        sb.setStyleSheet(f"""
            QStatusBar {{
                background-color: {C_STATUSBAR};
                color: #FFFFFF;
                font-size: 11px;
            }}
            QStatusBar::item {{
                border: none;
            }}
        """)
        sb.setFixedHeight(30)

        self.status_message = QLabel("Sẵn sàng")
        self.status_message.setStyleSheet("color: #FFFFFF; padding: 0 8px;")
        sb.addWidget(self.status_message, 1)

        self.status_progress = QProgressBar()
        self.status_progress.setFixedWidth(200)
        self.status_progress.setFixedHeight(10)
        self.status_progress.setRange(0, 100)
        self.status_progress.setValue(0)
        self.status_progress.setTextVisible(False)
        sb.addPermanentWidget(self.status_progress)

        self.status_screen = QLabel("Màn hình: —")
        self.status_screen.setStyleSheet("color: #9DB4D6; padding: 0 12px;")
        sb.addPermanentWidget(self.status_screen)

    # ==================================================================
    # PUBLIC API — Controller gọi các hàm này
    # ==================================================================
    def update_status(
        self,
        message: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> None:
        """Cập nhật statusbar. Gọi từ main thread (hoặc qua QMetaObject)."""
        if message is not None:
            self.status_message.setText(message)
        if progress is not None:
            try:
                p = max(0, min(100, int(float(progress))))
            except Exception:
                p = 0
            self.status_progress.setValue(p)

    def set_header_mode(self, text: str) -> None:
        """Cập nhật tên màn hình trên header và statusbar."""
        self._lbl_header_mode.setText(text)
        self.status_screen.setText(f"Màn hình: {text}")

    def set_export_enabled(self, enabled: bool) -> None:
        """Bật/tắt nút Export từ Controller."""
        self.btn_export.setEnabled(enabled)

    def get_current_theme(self) -> str:
        """Trả về tên theme hiện tại ('Light' | 'Dark')."""
        return self._ui_settings.get("theme", "Light")

    def apply_theme(self, theme: str) -> None:
        """Ghi nhớ theme vào settings (không thay đổi stylesheet trong v5.0)."""
        self._ui_settings["theme"] = theme
        self._save_settings()
        self.update_status(message=f"Đã chuyển theme: {theme}")

    def get_shortcut(self, key: str, default: str) -> str:
        return (self._ui_settings.get("shortcuts") or {}).get(key, default)

    def get_ui_customization(self, key: str, default: str = "") -> str:
        """Lấy giá trị cấu hình giao diện. Nếu chưa có thì trả về default."""
        custom = self._ui_settings.get("ui_customization") or {}
        return custom.get(key, default)

    def save_ui_customization(self, values: dict) -> None:
        """Lưu cấu hình giao diện vào settings.json."""
        if "ui_customization" not in self._ui_settings:
            self._ui_settings["ui_customization"] = {}
        self._ui_settings["ui_customization"].update(values)
        self._save_settings()

    # ==================================================================
    # HELPER TẠO WIDGET CHUẨN (dùng trong các Screen)
    # ==================================================================
    @staticmethod
    def make_primary_btn(
        text: str,
        width: int = 200,
        height: int = 42,
    ) -> QPushButton:
        """Tạo QPushButton màu primary (xanh đậm)."""
        return _styled_btn(
            text, bg=C_PRIMARY, hover_bg=C_SIDEBAR_ACT,
            width=width, height=height, bold=True, font_size=13,
        )

    @staticmethod
    def make_accent_btn(
        text: str,
        width: int = 200,
        height: int = 42,
    ) -> QPushButton:
        """Tạo QPushButton màu accent (cam)."""
        return _styled_btn(
            text, bg=C_ACCENT, hover_bg="#BF360C",
            width=width, height=height, bold=True, font_size=13,
        )

    @staticmethod
    def make_success_btn(
        text: str,
        width: int = 200,
        height: int = 42,
    ) -> QPushButton:
        """Tạo QPushButton màu success (xanh lá)."""
        return _styled_btn(
            text, bg=C_SUCCESS, hover_bg="#1B5E20",
            width=width, height=height, bold=True, font_size=13,
        )

    @staticmethod
    def make_ghost_btn(
        text: str,
        width: int = 160,
        height: int = 42,
    ) -> QPushButton:
        """Tạo QPushButton dạng ghost (viền, nền trong suốt)."""
        return _styled_btn(
            text, bg="transparent", fg=C_PRIMARY, hover_bg=C_BORDER,
            width=width, height=height, border=C_BORDER,
        )

    @staticmethod
    def make_card(parent: QWidget | None = None) -> QFrame:
        """Tạo QFrame dạng card (nền trắng, viền, bo góc)."""
        card = QFrame(parent)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {C_CARD};
                border: 1px solid {C_BORDER};
                border-radius: 12px;
            }}
        """)
        return card

    # ==================================================================
    # SETTINGS
    # ==================================================================
    def _default_settings(self) -> dict:
        return {
            "theme": "Light",
            "shortcuts": {
                "open":         "Ctrl+O",
                "save":         "Ctrl+S",
                "load_profile": "Ctrl+R",
                "export":       "Ctrl+E",
                "help":         "F1",
            },
            "ui_customization": {
                "welcome_title":        "Chào mừng đến DataMerge Pro",
                "welcome_subtitle":     "Hợp nhất & chuẩn hóa dữ liệu Excel nhanh chóng, chính xác và bảo mật tuyệt đối.",
                "card_person_title":    "Gộp hồ sơ người",
                "card_person_subtitle": "Khử trùng & hợp nhất hồ sơ nhân sự",
                "card_goods_title":     "Gộp hàng hóa thông minh",
                "card_goods_subtitle":  "Chuẩn hóa tên sản phẩm bằng AI",
            },
        }

    def _load_settings(self) -> None:
        try:
            if self._settings_path.exists():
                self._ui_settings = json.loads(
                    self._settings_path.read_text(encoding="utf-8")
                )
            else:
                self._ui_settings = self._default_settings()
        except Exception:
            self._ui_settings = self._default_settings()

    def _save_settings(self) -> None:
        try:
            self._settings_path.write_text(
                json.dumps(self._ui_settings, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"[settings] save failed: {e}")
