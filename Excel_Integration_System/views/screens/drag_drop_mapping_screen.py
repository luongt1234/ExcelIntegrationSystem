"""
views/screens/drag_drop_mapping_screen.py
=========================================
Màn hình Ghép Cột (Click-to-Pair) – bước trung gian giữa StructureConfirmScreen
và DedupConfigScreen (Mode 1) hoặc Left Join (Mode 2).

Kiến trúc:
    PreviewTableModel      – model bảng xem trước File Phụ (kế thừa ExcelTableModel),
                              hỗ trợ đổi tên Header khi cột được ghép đôi.
    MasterColumnSlot        – slot đại diện cho 1 cột File Gốc, nhận Click để ghép.
    DragDropMappingScreen   – màn hình tổng hợp, điều phối luồng Click-to-Pair.

Quy tắc:
    - View KHÔNG import Controller.
    - Tất cả trạng thái nội bộ che sau DTO Getter.
    - Cột File Phụ chưa ghép → BỎ QUA (không đưa vào kết quả).
    - Mỗi File Phụ có 1 Tab riêng trong QTabWidget (khung phải), hiển thị
      toàn bộ DataFrame dưới dạng bảng tính (giống Excel thực tế).
    - Click vào Header cột (khung phải) → chọn cột phụ đang "chờ ghép" (pending).
    - Click vào MasterColumnSlot (khung trái) → ghép cột phụ đang pending vào đó.
    - Tên class màn hình vẫn giữ "DragDropMappingScreen" để Controller/AppController
      hiện hữu không cần đổi tên import/khởi tạo.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import pandas as pd

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QTabWidget,
    QTableView,
    QHeaderView,
)

from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_SUCCESS, C_DANGER,
    C_WARN, C_CARD, C_BORDER, C_BG_LIGHT, C_TEXT_MUTED, C_SIDEBAR_ACT,
    _qfont, _styled_btn,
)

from models.excel_table_model import ExcelTableModel

# ── Palette màu cho các File Phụ (xoay vòng) ────────────────────────────────
AUX_FILE_PALETTE: List[Tuple[str, str, str]] = [
    # (bg_card, border, text_light)
    ("#E65100", "#BF360C", "#FFFFFF"),   # Cam đậm
    ("#6A1B9A", "#4A148C", "#FFFFFF"),   # Tím
    ("#00695C", "#004D40", "#FFFFFF"),   # Xanh ngọc
    ("#1565C0", "#0D47A1", "#FFFFFF"),   # Xanh dương (dự phòng)
    ("#AD1457", "#880E4F", "#FFFFFF"),   # Hồng đậm
    ("#F57F17", "#E65100", "#FFFFFF"),   # Vàng cam
]

MASTER_COLOR    = "#1B3A6B"   # màu File Gốc
MATCHED_BORDER  = "#2E7D32"   # viền xanh khi đã ghép
PENDING_BORDER  = "#1565C0"   # viền xanh dương khi cột phụ đang chờ ghép
UNMATCHED_BG    = "#F5F7FA"


# ══════════════════════════════════════════════════════════════════════════════
# 1. PREVIEW TABLE MODEL — model bảng xem trước File Phụ, hỗ trợ đổi Header
# ══════════════════════════════════════════════════════════════════════════════
class PreviewTableModel(ExcelTableModel):
    """
    Kế thừa ExcelTableModel để hiển thị toàn bộ DataFrame của 1 File Phụ
    dưới dạng bảng tính (giống Excel thực tế) trong QTableView.

    Bổ sung khả năng đổi tên Header hiển thị (không đổi tên cột thật trong
    DataFrame) để báo cho người dùng biết cột đó đã được ghép vào cột nào
    bên File Gốc.

    Thuộc tính:
        _header_overrides – Dict[int, str] ánh xạ {col_index: header_text_hiển_thị}
        _original_headers – list tên cột gốc (lưu lại để khôi phục khi hủy ghép)

    LƯU Ý TÍCH HỢP:
        Class này giả định ExcelTableModel(dataframe, parent=None) là kiểu khởi
        tạo cơ sở (nhận trực tiếp 1 pandas.DataFrame) và đã tự cung cấp
        rowCount()/columnCount()/data(). Nếu signature thực tế của
        ExcelTableModel trong dự án khác (VD: nhận thêm tham số khác), chỉnh
        lại __init__ bên dưới cho khớp — phần override headerData/
        update_header_text không phụ thuộc vào chi tiết đó.
    """

    def __init__(self, dataframe: pd.DataFrame, parent=None) -> None:
        super().__init__(parent)
        self.load_data(dataframe)
        self._original_headers: List[str] = [str(c) for c in dataframe.columns]
        self._header_overrides: Dict[int, str] = {}

    # ── API chính: đổi / khôi phục Header hiển thị ───────────────────────────
    def update_header_text(self, col_idx: int, new_text: Optional[str]) -> None:
        """
        Đổi text hiển thị của Header tại cột col_idx.
        new_text = None hoặc "" → khôi phục về tên cột gốc.
        """
        if col_idx < 0 or col_idx >= len(self._original_headers):
            return

        if not new_text:
            self._header_overrides.pop(col_idx, None)
        else:
            self._header_overrides[col_idx] = new_text

        self.headerDataChanged.emit(Qt.Orientation.Horizontal, col_idx, col_idx)

    def header_text_for(self, col_idx: int) -> str:
        """Trả về tên cột GỐC (không bị ghi đè) cho 1 chỉ số cột."""
        if 0 <= col_idx < len(self._original_headers):
            return self._original_headers[col_idx]
        return ""

    def col_index_for_header(self, original_name: str) -> int:
        """Tìm chỉ số cột theo tên cột GỐC (dùng khi auto-map / khôi phục)."""
        try:
            return self._original_headers.index(original_name)
        except ValueError:
            return -1

    def is_paired(self, col_idx: int) -> bool:
        return col_idx in self._header_overrides

    # ── Override headerData ──────────────────────────────────────────────────
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                if section in self._header_overrides:
                    return self._header_overrides[section]
                return self.header_text_for(section)
            if role == Qt.ItemDataRole.ForegroundRole:
                if section in self._header_overrides:
                    return QColor(MATCHED_BORDER)
        return super().headerData(section, orientation, role)


# ══════════════════════════════════════════════════════════════════════════════
# 2. MASTER COLUMN SLOT — slot Click-to-Pair (cột File Gốc)
# ══════════════════════════════════════════════════════════════════════════════
class MasterColumnSlot(QFrame):
    """
    Slot cố định bên trái, đại diện cho 1 cột File Gốc.
    Nhận Click chuột để ghép với cột phụ đang ở trạng thái "chờ ghép" (pending).

    Signal:
        slot_clicked(col_name)
            - Phát ra khi user click trái vào slot. DragDropMappingScreen sẽ
              quyết định có ghép được hay không (tùy có pending_aux không).
        pair_changed(master_col, aux_col, file_path, file_index)
            - Khi ghép xong (aux_col != "") hoặc hủy ghép.
              Khi HỦY ghép, aux_col mang giá trị "" còn tên cột phụ vừa bị
              hủy được phát kèm qua aux_col_removed (xem unpair_requested).
        unpair_requested(master_col, removed_aux_col, file_path)
            - Phát ra NGAY TRƯỚC khi state bị xóa, để màn hình còn kịp biết
              tên cột phụ gốc để khôi phục Header bên bảng phải.
    """

    slot_clicked = pyqtSignal(str)
    pair_changed = pyqtSignal(str, str, str, int)
    unpair_requested = pyqtSignal(str, str, str)

    def __init__(self, col_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.col_name  = col_name
        self._paired_aux_col:   str = ""
        self._paired_file_path: str = ""
        self._paired_file_idx:  int = -1
        self._paired_col_idx:   int = -1     # chỉ số cột trong PreviewTableModel
        self.is_key: bool = False
        self.is_pending_target: bool = False  # True khi đang có aux pending sẵn sàng ghép vào đây

        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._build_ui()
        self._refresh_style()

    def _build_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 8, 4)
        lay.setSpacing(6)

        # Nhãn cột gốc
        self._lbl_master = QLabel(self.col_name)
        self._lbl_master.setFont(_qfont("Segoe UI", 11, bold=True))
        self._lbl_master.setStyleSheet(f"color: {MASTER_COLOR}; background: transparent; border: none;")
        self._lbl_master.setMinimumWidth(120)
        lay.addWidget(self._lbl_master)

        # Mũi tên
        lbl_arrow = QLabel("←")
        lbl_arrow.setFont(_qfont("Segoe UI", 12))
        lbl_arrow.setStyleSheet(f"color: {C_TEXT_MUTED}; background: transparent; border: none;")
        lay.addWidget(lbl_arrow)

        # Badge thể hiện cột phụ đã ghép / trạng thái
        self._badge = QLabel("⬜ Click để chọn cột ghép…")
        self._badge.setFont(_qfont("Segoe UI", 10))
        self._badge.setStyleSheet(f"color: {C_TEXT_MUTED}; background: transparent; border: none;")
        lay.addWidget(self._badge, stretch=1)

        # Nút đánh dấu làm khóa (ẩn khi chưa ghép)
        self._btn_key = QPushButton("🔑 Khóa")
        self._btn_key.setToolTip("Đánh dấu làm Khóa đối chiếu (VD: CCCD, Mã NV)")
        self._btn_key.setFixedHeight(24)
        self._btn_key.setStyleSheet("""
            QPushButton {
                background: #EEEEEE; border: 1px solid #CCCCCC; border-radius: 4px;
                color: #555555; font-size: 11px; padding: 0 8px;
            }
            QPushButton:hover { background: #E0E0E0; }
        """)
        self._btn_key.setVisible(False)
        self._btn_key.clicked.connect(self.toggle_key)
        lay.addWidget(self._btn_key)

        # Nút hủy ghép (ẩn khi chưa ghép)
        self._btn_clear = QPushButton("✕")
        self._btn_clear.setFixedSize(22, 22)
        self._btn_clear.setStyleSheet("""
            QPushButton {
                background: #FFCDD2; border: none; border-radius: 11px;
                color: #C62828; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background: #EF9A9A; }
        """)
        self._btn_clear.setVisible(False)
        self._btn_clear.clicked.connect(self.clear_pair)
        lay.addWidget(self._btn_clear)

    def _refresh_style(self) -> None:
        paired = bool(self._paired_aux_col)

        if paired:
            palette_idx = self._paired_file_idx % len(AUX_FILE_PALETTE)
            badge_bg, badge_border, badge_fg = AUX_FILE_PALETTE[palette_idx]

            # Đổi style nếu là Khóa đối chiếu
            if self.is_key:
                frame_bg = "#FFF8E1"
                frame_border = "#FFB300"
                self._btn_key.setStyleSheet("""
                    QPushButton {
                        background: #FFECB3; border: 1px solid #FFB300; border-radius: 4px;
                        color: #FF8F00; font-size: 11px; font-weight: bold; padding: 0 8px;
                    }
                    QPushButton:hover { background: #FFE082; }
                """)
            else:
                frame_bg = "#F1F8E9"
                frame_border = MATCHED_BORDER
                self._btn_key.setStyleSheet("""
                    QPushButton {
                        background: #EEEEEE; border: 1px solid #CCCCCC; border-radius: 4px;
                        color: #555555; font-size: 11px; padding: 0 8px;
                    }
                    QPushButton:hover { background: #E0E0E0; }
                """)

            self.setStyleSheet(f"""
                QFrame {{
                    background: {frame_bg};
                    border: 2px solid {frame_border};
                    border-radius: 6px;
                }}
            """)
            self._badge.setText(f"🔗 {self._paired_aux_col}")
            self._badge.setStyleSheet(f"""
                color: {badge_bg};
                background: transparent;
                border: none;
                font-weight: bold;
            """)
            self._btn_key.setVisible(True)
            self._btn_clear.setVisible(True)

        elif self.is_pending_target:
            # Có 1 cột phụ đang chờ ghép → mời người dùng click vào đây
            self.setStyleSheet(f"""
                QFrame {{
                    background: #E3F2FD;
                    border: 2px solid {PENDING_BORDER};
                    border-radius: 6px;
                }}
            """)
            self._badge.setText("👉 Click để ghép cột đang chọn vào đây")
            self._badge.setStyleSheet(f"color: {PENDING_BORDER}; background: transparent; border: none; font-weight: bold;")
            self._btn_key.setVisible(False)
            self._btn_clear.setVisible(False)

        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {UNMATCHED_BG};
                    border: 2px dashed {C_BORDER};
                    border-radius: 6px;
                }}
            """)
            self._badge.setText("⬜ Click để chọn cột ghép…")
            self._badge.setStyleSheet(f"color: {C_TEXT_MUTED}; background: transparent; border: none;")
            self._btn_key.setVisible(False)
            self._btn_clear.setVisible(False)

    def set_pending_target(self, is_pending: bool) -> None:
        """Đánh dấu slot này có thể nhận ghép (có 1 cột phụ đang pending)."""
        if self.is_paired:
            return   # Slot đã ghép thì không cần hiển thị trạng thái pending
        self.is_pending_target = is_pending
        self._refresh_style()

    def toggle_key(self) -> None:
        """Bật/tắt trạng thái Khóa đối chiếu."""
        if self._paired_aux_col:
            self.is_key = not self.is_key
            self._refresh_style()

    # ── Pair management ──────────────────────────────────────────────────────
    def set_pair(self, aux_col: str, file_path: str, file_index: int, col_idx: int = -1) -> None:
        """Ghép cột phụ vào slot này."""
        self._paired_aux_col   = aux_col
        self._paired_file_path = file_path
        self._paired_file_idx  = file_index
        self._paired_col_idx   = col_idx
        self.is_pending_target = False
        self._refresh_style()
        self.pair_changed.emit(self.col_name, aux_col, file_path, file_index)

    def clear_pair(self) -> None:
        """
        Hủy ghép. Phát unpair_requested TRƯỚC khi xóa state, mang đầy đủ
        thông tin cột phụ vừa bị hủy để màn hình khôi phục Header bên phải.
        """
        old_aux  = self._paired_aux_col
        old_fp   = self._paired_file_path
        old_idx  = self._paired_file_idx

        if old_aux:
            self.unpair_requested.emit(self.col_name, old_aux, old_fp)

        self._paired_aux_col   = ""
        self._paired_file_path = ""
        self._paired_file_idx  = -1
        self._paired_col_idx   = -1
        self.is_key            = False
        self.is_pending_target = False

        self._refresh_style()

        self.pair_changed.emit(self.col_name, "", old_fp, old_idx)

    @property
    def is_paired(self) -> bool:
        return bool(self._paired_aux_col)

    def get_pair(self) -> Tuple[str, str, str, int]:
        """(master_col, aux_col, file_path, file_index)"""
        return (self.col_name, self._paired_aux_col,
                self._paired_file_path, self._paired_file_idx)

    # ── Click-to-Pair: phát tín hiệu khi click ───────────────────────────────
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.slot_clicked.emit(self.col_name)
        super().mousePressEvent(event)


# ══════════════════════════════════════════════════════════════════════════════
# 3. DRAG DROP MAPPING SCREEN — màn hình tổng hợp (Click-to-Pair)
# ══════════════════════════════════════════════════════════════════════════════
class DragDropMappingScreen(QWidget):
    """
    Màn hình ghép cột Click-to-Pair.

    Luồng:
        StructureConfirmScreen ──► DragDropMappingScreen ──► (intent buttons)
            ├── btn_back → AppController.show_structure_confirm(...)
            └── btn_next → Controller.handle_drag_drop_confirmed(self)

    DTO Getters (giữ nguyên hợp đồng với Controller):
        get_column_mapping()    → Dict[str, str]             {aux_col: master_col}
        get_key_columns()       → List[str]                  cột File Gốc làm khóa
        get_unmapped_aux_cols() → List[str]                  cột phụ chưa ghép (bỏ qua)
        get_paired_slots()      → List[Tuple[str, str, str]] [(master_col, aux_col, file_path)]

    Params:
        master_cols               – list tên cột File Gốc (từ file_structures[0])
        aux_cols_by_file          – Dict[file_path, List[str]] cột từng File Phụ
        pre_confirmed_structures  – Dict[file_path, dict] cấu trúc đã xác nhận
                                     (sheet_name, header_row, ...) cho TẤT CẢ file,
                                     dùng để nạp DataFrame xem trước giống Excel thực.
    """

    def __init__(
        self,
        window: MainWindow,
        master_cols: List[str],
        aux_cols_by_file: Dict[str, List[str]],
        pre_confirmed_structures: Optional[Dict[str, dict]] = None,
    ) -> None:
        super().__init__()
        self._window              = window
        self._master_cols         = master_cols
        self._aux_cols_by_file    = aux_cols_by_file  # {file_path: [col, ...]}
        self._file_structures     = pre_confirmed_structures or {}

        # Danh sách file phụ theo thứ tự (để gán màu nhất quán)
        self._aux_files: List[str] = list(aux_cols_by_file.keys())

        # Registry: slot objects {master_col: slot}
        self._slots: Dict[str, MasterColumnSlot] = {}

        # Registry: 1 PreviewTableModel + 1 QTableView cho mỗi file phụ
        self._table_models: Dict[str, PreviewTableModel] = {}   # {file_path: model}
        self._table_views:  Dict[str, QTableView] = {}           # {file_path: view}

        # ── State Click-to-Pair ───────────────────────────────────────────
        self._pending_aux_col: str = ""
        self._pending_file_path: str = ""
        self._pending_col_idx: int = -1
        self._pending_table_model: Optional[PreviewTableModel] = None

        self._build_ui()
        self._auto_map()

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)

        # Step bar
        root.addWidget(self._make_step_bar())

        # Header
        hdr = QLabel("BƯỚC 2 / 3  –  GHÉP CỘT & CHỌN HƯỚNG XỬ LÝ")
        hdr.setFont(_qfont("Segoe UI", 16, bold=True))
        hdr.setStyleSheet(f"color: {C_PRIMARY};")
        root.addWidget(hdr)

        info = self._make_info_box(
            "🖱️  Click vào tên cột trên bảng bên phải để chọn cột cần ghép.\n"
            "     Sau đó Click vào ô bên trái (File Gốc) để hoàn tất ghép đôi.\n"
            "     Các cột trùng tên đã được ghép tự động. Cột chưa ghép sẽ được chèn thêm thành cột mới.\n"
            "     Bấm 🔑 Khóa để chọn cột làm Khóa đối chiếu."
        )
        root.addWidget(info)

        # Main splitter: left (master slots) + right (aux preview tables)
        body = QHBoxLayout()
        body.setSpacing(12)

        body.addWidget(self._make_master_panel(), stretch=3)
        body.addWidget(self._make_aux_panel(), stretch=4)

        root.addLayout(body, stretch=1)

        # Status bar
        self._lbl_status = QLabel("")
        self._lbl_status.setFont(_qfont("Segoe UI", 11))
        self._lbl_status.setStyleSheet(f"color: {C_TEXT_MUTED};")
        root.addWidget(self._lbl_status)

        # Intent buttons
        root.addLayout(self._make_intent_buttons())

    def _make_step_bar(self) -> QFrame:
        bar = QFrame()
        bar.setStyleSheet("background: #EEF2FF; border-radius: 8px;")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 6, 16, 6)
        for text, active in [
            ("① Xác nhận cấu trúc", False),
            ("② Ghép cột & Chọn hướng", True),
            ("③ Xử lý & Xuất kết quả", False),
        ]:
            lbl = QLabel(text)
            lbl.setFont(_qfont("Segoe UI", 12, bold=active))
            color = "#1565C0" if active else "#9E9E9E"
            lbl.setStyleSheet(f"color: {color}; background: transparent;")
            lay.addWidget(lbl)
            lay.addSpacing(20)
        lay.addStretch()
        return bar

    @staticmethod
    def _make_info_box(text: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background: #E3F2FD; border-radius: 6px; border: none;")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 8, 12, 8)
        lbl = QLabel(text)
        lbl.setFont(_qfont("Segoe UI", 11))
        lbl.setStyleSheet("color: #1565C0; background: transparent; border: none;")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        return frame

    def _make_master_panel(self) -> QWidget:
        """Panel bên trái: danh sách MasterColumnSlot."""
        wrapper = QFrame()
        wrapper.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 1px solid {C_BORDER};
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        icon_lbl = QLabel("📋")
        icon_lbl.setFont(_qfont("Segoe UI", 16))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        title = QLabel("Cột File Gốc  (Click để ghép)")
        title.setFont(_qfont("Segoe UI", 13, bold=True))
        title.setStyleSheet(f"color: {MASTER_COLOR}; background: transparent; border: none;")
        hdr.addWidget(icon_lbl)
        hdr.addWidget(title)
        hdr.addStretch()
        lay.addLayout(hdr)

        # Subtitle
        sub = QLabel(f"{len(self._master_cols)} cột")
        sub.setFont(_qfont("Segoe UI", 10))
        sub.setStyleSheet(f"color: {C_TEXT_MUTED}; background: transparent; border: none;")
        lay.addWidget(sub)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vlay = QVBoxLayout(container)
        vlay.setSpacing(4)
        vlay.setContentsMargins(0, 0, 4, 0)

        for col in self._master_cols:
            slot = MasterColumnSlot(col, parent=self)
            slot.pair_changed.connect(self._on_pair_changed)
            slot.slot_clicked.connect(self._on_slot_clicked)
            slot.unpair_requested.connect(self._on_unpair_requested)
            self._slots[col] = slot
            vlay.addWidget(slot)

        vlay.addStretch()
        scroll.setWidget(container)
        lay.addWidget(scroll, stretch=1)

        return wrapper

    def _make_aux_panel(self) -> QWidget:
        """
        Panel bên phải: QTabWidget, mỗi Tab là 1 File Phụ hiển thị toàn bộ
        DataFrame dưới dạng bảng tính (QTableView) giống Excel thực tế.
        """
        wrapper = QFrame()
        wrapper.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 1px solid {C_BORDER};
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        icon_lbl = QLabel("📎")
        icon_lbl.setFont(_qfont("Segoe UI", 16))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        title = QLabel("File Phụ  (Click vào Header cột để chọn)")
        title.setFont(_qfont("Segoe UI", 13, bold=True))
        title.setStyleSheet(f"color: {C_ACCENT}; background: transparent; border: none;")
        hdr.addWidget(icon_lbl)
        hdr.addWidget(title)
        hdr.addStretch()
        lay.addLayout(hdr)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {C_BORDER};
                border-radius: 6px;
                background: white;
            }}
            QTabBar::tab {{
                padding: 6px 14px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: {UNMATCHED_BG};
                color: {C_TEXT_MUTED};
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {C_PRIMARY};
                font-weight: bold;
            }}
        """)

        for fi, fp in enumerate(self._aux_files):
            cols = self._aux_cols_by_file.get(fp, [])
            if not cols:
                continue

            df = self._load_dataframe_for(fp, cols)

            table_view = QTableView()
            table_view.setFont(_qfont("Segoe UI", 10))
            table_view.setAlternatingRowColors(True)
            table_view.horizontalHeader().setStretchLastSection(False)
            table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            table_view.horizontalHeader().setDefaultSectionSize(130)
            table_view.verticalHeader().setVisible(True)
            table_view.verticalHeader().setDefaultSectionSize(30)
            table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectColumns)
            table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

            model = PreviewTableModel(df, parent=table_view)
            table_view.setModel(model)

            self._table_models[fp] = model
            self._table_views[fp] = table_view

            # Bắt sự kiện Click vào Header cột
            table_view.horizontalHeader().sectionClicked.connect(
                lambda logical_idx, _fp=fp, _fi=fi: self._on_aux_header_clicked(_fp, _fi, logical_idx)
            )

            tab_label = f"{os.path.basename(fp)}"
            palette_idx = fi % len(AUX_FILE_PALETTE)
            tabs.addTab(table_view, tab_label)

            # Tô màu chữ trên tab theo palette của file (giúp phân biệt nhanh)
            bg, border, fg = AUX_FILE_PALETTE[palette_idx]
            tabs.tabBar().setTabTextColor(tabs.indexOf(table_view), QColor(border))

        lay.addWidget(tabs, stretch=1)
        self._tabs = tabs

        return wrapper

    def _load_dataframe_for(self, file_path: str, fallback_cols: List[str]) -> pd.DataFrame:
        """
        Nạp DataFrame xem trước cho 1 File Phụ.

        Ưu tiên dùng cấu trúc đã xác nhận (self._file_structures) qua
        DataProcessor.load_clean_flat_data(struct) để đảm bảo đúng sheet /
        dòng tiêu đề / kiểu dữ liệu đã làm sạch. Nếu không có cấu trúc,
        fallback đọc thô bằng pandas, rồi nếu vẫn lỗi, dựng DataFrame rỗng
        chỉ với danh sách cột đã biết (để UI không bị crash).
        """
        struct = self._file_structures.get(file_path)

        if struct:
            try:
                from services.data_processor import DataProcessor
                processor = DataProcessor(None)
                df = processor.load_clean_flat_data(struct)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return df
            except Exception as e:
                print(f"Error loading clean flat data: {e}")

        # Fallback: đọc thô bằng pandas theo sheet/header đã xác nhận (nếu có)
        try:
            sheet = (struct or {}).get("sheet_name", 0)
            header_row = (struct or {}).get("header_row", 0)
            df = pd.read_excel(file_path, sheet_name=sheet, header=header_row)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception:
            # Fallback cuối: DataFrame rỗng chỉ có header đã biết, để UI vẫn hiển thị được
            return pd.DataFrame(columns=fallback_cols)

    def _make_file_legend(self, parent_lay: QVBoxLayout) -> None:
        """Chú thích màu sắc từng file phụ (giữ lại để dùng nếu cần ở nơi khác)."""
        if len(self._aux_files) <= 1:
            return
        row = QHBoxLayout()
        row.setSpacing(8)
        for fi, fp in enumerate(self._aux_files):
            palette_idx = fi % len(AUX_FILE_PALETTE)
            bg, border, fg = AUX_FILE_PALETTE[palette_idx]
            chip = QLabel(f"  {os.path.basename(fp)[:18]}  ")
            chip.setFont(_qfont("Segoe UI", 9))
            chip.setStyleSheet(f"""
                color: {fg};
                background: {bg};
                border-radius: 4px;
                padding: 1px 4px;
                border: none;
            """)
            row.addWidget(chip)
        row.addStretch()
        parent_lay.addLayout(row)

    def _make_intent_buttons(self) -> QHBoxLayout:
        """2 nút ý định + nút Quay lại."""
        lay = QHBoxLayout()
        lay.setSpacing(12)

        self.btn_back = _styled_btn(
            "◀  Quay lại xác nhận cấu trúc",
            bg="#546E7A", hover_bg="#37474F",
            width=240, height=42,
        )

        lay.addWidget(self.btn_back)
        lay.addStretch()

        self._lbl_match_count = QLabel("")
        self._lbl_match_count.setFont(_qfont("Segoe UI", 11))
        self._lbl_match_count.setStyleSheet(f"color: {C_SUCCESS};")
        lay.addWidget(self._lbl_match_count)

        self.btn_next = _styled_btn(
            "🚀 Bắt đầu Bổ Sung Thông Tin",
            bg=C_PRIMARY, hover_bg=C_SIDEBAR_ACT,
            width=260, height=46, bold=True, font_size=13,
        )

        lay.addWidget(self.btn_next)
        return lay

    # ── Click-to-Pair: lựa chọn cột phụ (pending) ────────────────────────────
    def _on_aux_header_clicked(self, file_path: str, file_index: int, logical_idx: int) -> None:
        """User click vào Header 1 cột trên bảng xem trước (khung phải)."""
        model = self._table_models.get(file_path)
        table_view = self._table_views.get(file_path)
        if model is None or table_view is None:
            return

        # Nếu cột này đã được ghép rồi → không cho chọn lại làm pending
        if model.is_paired(logical_idx):
            QMessageBox.information(
                self,
                "Cột đã ghép",
                "Cột này đã được ghép vào File Gốc.\n"
                "Bấm ✕ trên ô File Gốc tương ứng để hủy ghép trước khi chọn lại.",
            )
            return

        col_name = model.header_text_for(logical_idx)

        self._pending_aux_col     = col_name
        self._pending_file_path   = file_path
        self._pending_col_idx     = logical_idx
        self._pending_table_model = model

        # Highlight cột đang chọn
        table_view.selectColumn(logical_idx)

        # Báo cho tất cả slot trái biết: đang có 1 cột pending → có thể nhận ghép
        for slot in self._slots.values():
            slot.set_pending_target(True)

        self._update_status()

    # ── Click-to-Pair: ghép vào MasterColumnSlot ─────────────────────────────
    def _on_slot_clicked(self, master_col: str) -> None:
        """User click vào 1 MasterColumnSlot (khung trái)."""
        slot = self._slots.get(master_col)
        if slot is None:
            return

        if not self._pending_aux_col or self._pending_table_model is None:
            # Không có cột phụ nào đang chờ ghép → không làm gì cả
            return

        # Nếu slot này đã có cặp ghép khác → hủy trước khi ghép cặp mới
        # (clear_pair() sẽ tự phát unpair_requested → khôi phục Header cũ)
        if slot.is_paired:
            slot.clear_pair()

        aux_col    = self._pending_aux_col
        file_path  = self._pending_file_path
        col_idx    = self._pending_col_idx
        file_index = self._aux_files.index(file_path) if file_path in self._aux_files else -1

        slot.set_pair(aux_col, file_path, file_index, col_idx)

        # Cập nhật Header bên bảng phải: chữ xanh + ghi chú đã ghép vào cột nào
        self._pending_table_model.update_header_text(
            col_idx, f"{aux_col}\n[Đã ghép ✅ → {master_col}]"
        )

        self._clear_pending_state()
        self._update_status()

    def _clear_pending_state(self) -> None:
        self._pending_aux_col = ""
        self._pending_file_path = ""
        self._pending_col_idx = -1
        self._pending_table_model = None
        for slot in self._slots.values():
            slot.set_pending_target(False)

    def _on_unpair_requested(self, master_col: str, removed_aux_col: str, file_path: str) -> None:
        """
        Slot sắp hủy ghép (qua nút ✕ hoặc khi bị ghép đè bởi cặp mới) →
        khôi phục Header gốc bên PreviewTableModel tương ứng.
        """
        model = self._table_models.get(file_path)
        if model is None:
            return
        col_idx = model.col_index_for_header(removed_aux_col)
        if col_idx >= 0:
            model.update_header_text(col_idx, None)

    def _on_pair_changed(self, master_col: str, aux_col: str, file_path: str, file_idx: int) -> None:
        """Cập nhật status bar mỗi khi 1 slot ghép xong hoặc hủy ghép."""
        self._update_status()

    def _update_status(self) -> None:
        paired = sum(1 for s in self._slots.values() if s.is_paired)
        total  = len(self._slots)
        unmapped_aux = len(self.get_unmapped_aux_cols())

        pending_note = ""
        if self._pending_aux_col:
            pending_note = f"   •   👉 Đang chọn: \"{self._pending_aux_col}\" (click vào ô File Gốc để ghép)"

        self._lbl_status.setText(
            f"🔗 Đã ghép: {paired} / {total} cột File Gốc   •   "
            f"⬜ Cột phụ chưa ghép: {unmapped_aux} (sẽ bị bỏ qua){pending_note}"
        )
        if paired > 0:
            self._lbl_match_count.setText(f"✅ {paired} cặp đã ghép")
        else:
            self._lbl_match_count.setText("")

    # ── Auto-map ─────────────────────────────────────────────────────────────
    def _auto_map(self) -> None:
        """
        Tự động ghép các cột trùng tên (case-insensitive, strip) giữa
        File Gốc và các File Phụ. Cập nhật cả Slot trái và Header bảng phải.
        """
        master_lower = {col.strip().lower(): col for col in self._master_cols}

        for fi, fp in enumerate(self._aux_files):
            model = self._table_models.get(fp)
            if model is None:
                continue
            for col in self._aux_cols_by_file.get(fp, []):
                col_lower = col.strip().lower()
                if col_lower not in master_lower:
                    continue

                master_col = master_lower[col_lower]
                slot = self._slots.get(master_col)
                if slot is None or slot.is_paired:
                    continue

                col_idx = model.col_index_for_header(col)
                if col_idx < 0:
                    continue

                slot.set_pair(col, fp, fi, col_idx)
                model.update_header_text(col_idx, f"{col}\n[Đã ghép ✅ → {master_col}]")

        self._update_status()

    # ── Helper truy cập nội bộ (không phải DTO Getter, dùng nếu cần debug) ───
    def find_table_model(self, file_path: str) -> Optional[PreviewTableModel]:
        return self._table_models.get(file_path)

    # ── DTO Getters (giữ nguyên hợp đồng — Controller đang gọi các hàm này) ──
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Trả về dict ánh xạ: { aux_col_name: master_col_name }
        Chỉ chứa các cặp đã ghép.
        """
        result: Dict[str, str] = {}
        for master_col, slot in self._slots.items():
            if slot.is_paired:
                _, aux_col, _, _ = slot.get_pair()
                result[aux_col] = master_col
        return result

    def get_key_columns(self) -> List[str]:
        """
        Trả về danh sách các cột File Gốc được đánh dấu làm Khóa đối chiếu.
        """
        keys = []
        for master_col, slot in self._slots.items():
            if slot.is_paired and slot.is_key:
                keys.append(master_col)
        return keys

    def get_unmapped_aux_cols(self) -> List[str]:
        """Danh sách cột File Phụ chưa được ghép → sẽ bị bỏ qua."""
        mapped_aux = set(self.get_column_mapping().keys())
        unmapped = []
        for fp in self._aux_files:
            for col in self._aux_cols_by_file.get(fp, []):
                if col not in mapped_aux:
                    unmapped.append(col)
        return unmapped

    def get_paired_slots(self) -> List[Tuple[str, str, str]]:
        """Trả về [(master_col, aux_col, file_path), ...] các cặp đã ghép."""
        result = []
        for slot in self._slots.values():
            if slot.is_paired:
                master_col, aux_col, fp, _ = slot.get_pair()
                result.append((master_col, aux_col, fp))
        return result