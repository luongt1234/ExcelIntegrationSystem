import os
from typing import Dict, List, Optional

import pandas as pd
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_BORDER,
    C_TEXT_MUTED, C_CARD, C_SIDEBAR_ACT,
    _qfont, _styled_btn,
)

# Số dòng tối đa hiển thị trên bảng xem trước để đảm bảo hiệu năng UI.
# Khi xuất file, toàn bộ dữ liệu (self._full_df) vẫn được dùng, không bị cắt.
PREVIEW_MAX_ROWS = 1000


class DataCleanerScreen(QWidget):
    """
    Màn hình Cấu hình Dọn dẹp & Chuẩn hóa (Dành riêng cho Chế độ 3).
    Người dùng chọn các cột đánh dấu phân loại và chọn kiểu gộp.
    """

    def __init__(self, window: MainWindow, file_structures: Dict[str, dict]) -> None:
        super().__init__()
        self._window = window
        self._file_structures = file_structures
        
        # Lấy danh sách cột từ file đầu tiên (vì Mode 3 chỉ có 1 file)
        self._columns: List[str] = []
        if self._file_structures:
            first_key = list(self._file_structures.keys())[0]
            struct = self._file_structures[first_key]
            # Lấy danh sách tên cột gốc đã được mapping (không lấy những cột bị 'Bỏ qua')
            mapping = struct.get("column_mapping", {})
            self._columns = [
                k for k, v in mapping.items() 
                if v != "Bỏ qua (Ignore)"
            ]

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        root = QVBoxLayout(scroll_content)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(24)

        # ── Tiêu đề ─────────────────────────────────────────────
        lbl_title = QLabel("✨ Xử lý các cột đánh dấu (x)")
        lbl_title.setFont(_qfont("Segoe UI", 20, bold=True))
        lbl_title.setStyleSheet(f"color: {C_PRIMARY};")
        root.addWidget(lbl_title)

        lbl_sub = QLabel("Chọn các cột được dùng để đánh dấu phân loại (chỉ chứa các dấu x, v...) và chọn phương pháp quy hoạch.")
        lbl_sub.setFont(_qfont("Segoe UI", 11))
        lbl_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")
        lbl_sub.setWordWrap(True)
        root.addWidget(lbl_sub)

        # ── Bước 1: Chọn phương án xử lý (Hành động) ─────────────────────────
        step1_lbl = QLabel("1. Bạn muốn làm gì?")
        step1_lbl.setFont(_qfont("Segoe UI", 12, bold=True))
        root.addWidget(step1_lbl)

        methods_lay = QHBoxLayout()
        methods_lay.setSpacing(16)

        # Lựa chọn 1
        self.radio_keep = QRadioButton()
        card1 = self._build_method_card(
            self.radio_keep,
            "1. Dọn dẹp Bảng Đánh Dấu",
            "Giữ nguyên định dạng nhiều cột đánh dấu \"x\". Chỉ dồn các dòng lại cho gọn gàng.",
            "Tên | Viên chức | HĐLĐ\nNguyễn A | x | \nTrần B | x | \nLê C | | x"
        )
        methods_lay.addWidget(card1)

        # Lựa chọn 2
        self.radio_merge = QRadioButton()
        self.radio_merge.setChecked(True)
        card2 = self._build_method_card(
            self.radio_merge,
            "2. Chuyển thành Bảng Danh Sách",
            "Khuyên dùng: Gộp thành 1 cột chung. Xóa các cột X rườm rà, thay bằng 1 cột duy nhất chứa thẳng tên nhóm.",
            "Tên      | Loại nhân sự\nNguyễn A | Viên chức\nTrần B   | Viên chức\nLê C     | HĐLĐ"
        )
        methods_lay.addWidget(card2)

        # Lựa chọn 3
        self.radio_expand = QRadioButton()
        card3 = self._build_method_card(
            self.radio_expand,
            "3. Tạo Bảng Đánh Dấu mới",
            "Bung từ 1 cột ra nhiều cột X. Kẻ thêm các cột mới dựa trên tên nhóm và điền dấu x vào từng ô.",
            "Tên | Viên chức | HĐLĐ\nNguyễn A | x | \nTrần B | x | \nLê C | | x"
        )
        methods_lay.addWidget(card3)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_keep)
        self.mode_group.addButton(self.radio_merge)
        self.mode_group.addButton(self.radio_expand)

        root.addLayout(methods_lay)

        # ── Bước 2: Chọn cột ────────────────────────────
        self.step2_lbl = QLabel("2. Hãy tích chọn các cột đang chứa dấu (x)")
        self.step2_lbl.setFont(_qfont("Segoe UI", 12, bold=True))
        root.addWidget(self.step2_lbl)

        self.col_frame = QFrame()
        self.col_frame.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)
        self.col_lay = QVBoxLayout(self.col_frame)
        self.col_lay.setContentsMargins(16, 16, 16, 16)
        self.col_lay.setSpacing(8)
        
        self.col_content = QWidget()
        self.col_content.setStyleSheet("background: transparent;")
        self.col_lay.addWidget(self.col_content)

        root.addWidget(self.col_frame)
        root.addStretch()

        self._checkboxes = []
        self._radio_cols = []
        self._build_column_selector()

        self.radio_keep.toggled.connect(self._on_action_changed)
        self.radio_merge.toggled.connect(self._on_action_changed)
        self.radio_expand.toggled.connect(self._on_action_changed)

        # ── Bottom Nav ──────────────────────────────────────────
        nav = QHBoxLayout()
        self.btn_back = _styled_btn("◀  Quay lại", bg="#546E7A", hover_bg="#37474F", width=120, height=40)
        self.btn_clean = _styled_btn("✨ Thực hiện dọn dẹp", bg=C_PRIMARY, hover_bg=C_SIDEBAR_ACT, width=220, height=40, bold=True)

        nav.addWidget(self.btn_back)
        nav.addStretch()
        nav.addWidget(self.btn_clean)
        root.addLayout(nav)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _build_method_card(self, radio: QRadioButton, title: str, desc: str, table_text: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(320, 230)
        card.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 2px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        
        # Header (Radio + Title)
        h_lay = QHBoxLayout()
        radio.setCursor(Qt.CursorShape.PointingHandCursor)
        h_lay.addWidget(radio)
        
        lbl_t = QLabel(title)
        lbl_t.setFont(_qfont("Segoe UI", 12, bold=True))
        lbl_t.setStyleSheet("border: none;")
        lbl_t.setCursor(Qt.CursorShape.PointingHandCursor)
        h_lay.addWidget(lbl_t)
        h_lay.addStretch()
        lay.addLayout(h_lay)

        # Desc
        lbl_d = QLabel(desc)
        lbl_d.setFont(_qfont("Segoe UI", 10))
        lbl_d.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none;")
        lbl_d.setWordWrap(True)
        lay.addWidget(lbl_d)

        # Table example (HTML pre-styled)
        # We simulate a mini table using a label with monospace font
        lbl_table = QLabel(table_text)
        lbl_table.setFont(_qfont("Consolas", 10))
        lbl_table.setStyleSheet(f"background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; padding: 8px; color: #334155;")
        lbl_table.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(lbl_table)

        # Make card clickable to select radio
        def select_radio(event):
            radio.setChecked(True)
        
        card.mousePressEvent = select_radio
        lbl_t.mousePressEvent = select_radio
        lbl_d.mousePressEvent = select_radio
        lbl_table.mousePressEvent = select_radio

        return card

    def _on_action_changed(self):
        self._build_column_selector()

    def _build_column_selector(self):
        # Xóa các widget cũ
        if self.col_content:
            self.col_lay.removeWidget(self.col_content)
            self.col_content.deleteLater()

        self.col_content = QWidget()
        self.col_content.setStyleSheet("background: transparent;")
        grid_lay = QVBoxLayout(self.col_content)
        grid_lay.setContentsMargins(0, 0, 0, 0)
        self.col_lay.addWidget(self.col_content)

        self._checkboxes = []
        self._radio_cols = []

        if not self._columns:
            grid_lay.addWidget(QLabel("Không có cột nào được chọn từ bước trước."))
            return

        mode = self.get_clean_mode()
        struct = list(self._file_structures.values())[0] if self._file_structures else {}
        mapping = struct.get("column_mapping", {})
        core_cols = {"Họ và Tên", "Ngày Sinh", "Số CCCD/ID", "Số Điện Thoại", "Email", "Địa Chỉ", "STT", "Vị trí", "Đơn vị"}

        if mode in (1, 2):
            self.step2_lbl.setText("2. Hãy tích chọn các cột đang chứa dấu (x)")
            for col_name in self._columns:
                mapped_name = mapping.get(col_name)
                chk = QCheckBox(col_name)
                chk.setFont(_qfont("Segoe UI", 11))
                chk.setCursor(Qt.CursorShape.PointingHandCursor)
                
                if mapped_name in core_cols or str(col_name).strip().lower() == "stt":
                    chk.setChecked(False)
                else:
                    chk.setChecked(True)
                    
                self._checkboxes.append(chk)
                grid_lay.addWidget(chk)
        else: # mode 3
            self.step2_lbl.setText("2. Hãy chọn 1 cột đang chứa tên nhóm (ví dụ: Loại nhân sự)")
            # Set the first non-core column as default checked
            first_valid_set = False
            for col_name in self._columns:
                mapped_name = mapping.get(col_name)
                rdo = QRadioButton(col_name)
                rdo.setFont(_qfont("Segoe UI", 11))
                rdo.setCursor(Qt.CursorShape.PointingHandCursor)
                
                if not first_valid_set and (mapped_name not in core_cols and str(col_name).strip().lower() != "stt"):
                    rdo.setChecked(True)
                    first_valid_set = True
                    
                self._radio_cols.append(rdo)
                grid_lay.addWidget(rdo)
            
            if not first_valid_set and self._radio_cols:
                self._radio_cols[0].setChecked(True)

    def get_selected_columns(self) -> List[str]:
        """Trả về danh sách tên các cột được đánh dấu."""
        mode = self.get_clean_mode()
        if mode in (1, 2):
            return [chk.text() for chk in self._checkboxes if chk.isChecked()]
        else:
            return [rdo.text() for rdo in self._radio_cols if rdo.isChecked()]

    def get_clean_mode(self) -> int:
        """Trả về 1 (Giữ nhiều cột), 2 (Gộp thành 1 cột), hoặc 3 (Bung ra nhiều cột)."""
        if self.radio_keep.isChecked(): return 1
        if self.radio_expand.isChecked(): return 3
        return 2


class _PandasTableModel(QAbstractTableModel):
    """
    QAbstractTableModel mỏng để hiển thị pandas DataFrame trong QTableView.
    Chỉ đọc (read-only) — dùng cho mục đích xem trước (preview).
    """

    def __init__(self, df: pd.DataFrame, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.index)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            value = self._df.iat[index.row(), index.column()]
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return ""
            return str(value)
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)


class DataCleanerResultScreen(QWidget):
    """
    Màn hình Xem trước Kết quả Dọn dẹp & Chuẩn hóa (Chế độ 3).

    Hiển thị tối đa PREVIEW_MAX_ROWS dòng để đảm bảo hiệu năng UI,
    nhưng giữ toàn bộ DataFrame (self._full_df) để xuất file đầy đủ
    khi người dùng bấm "Xuất Excel".
    """

    def __init__(self, window: MainWindow, result_df: pd.DataFrame) -> None:
        super().__init__()
        self._window = window
        self._full_df = result_df
        self._is_truncated = len(result_df.index) > PREVIEW_MAX_ROWS
        self._preview_df = (
            result_df.head(PREVIEW_MAX_ROWS) if self._is_truncated else result_df
        )

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── Tiêu đề ─────────────────────────────────────────────
        lbl_title = QLabel("✅ Xem trước kết quả dọn dẹp")
        lbl_title.setFont(_qfont("Segoe UI", 20, bold=True))
        lbl_title.setStyleSheet(f"color: {C_PRIMARY};")
        root.addWidget(lbl_title)

        total_rows = len(self._full_df.index)
        total_cols = len(self._full_df.columns)
        if self._is_truncated:
            sub_text = (
                f"Đã chuẩn hóa {total_rows:,} dòng, {total_cols} cột. "
                f"Chỉ hiển thị {PREVIEW_MAX_ROWS:,} dòng đầu để đảm bảo hiệu năng "
                f"— file xuất ra vẫn có đầy đủ {total_rows:,} dòng."
            )
        else:
            sub_text = f"Đã chuẩn hóa {total_rows:,} dòng, {total_cols} cột."
        lbl_sub = QLabel(sub_text)
        lbl_sub.setFont(_qfont("Segoe UI", 11))
        lbl_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")
        lbl_sub.setWordWrap(True)
        root.addWidget(lbl_sub)

        # ── Bảng xem trước ───────────────────────────────────────
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)
        table_lay = QVBoxLayout(table_frame)
        table_lay.setContentsMargins(1, 1, 1, 1)

        self.table_view = QTableView()
        self.table_view.setModel(_PandasTableModel(self._preview_df, self))
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setFont(_qfont("Segoe UI", 10))
        table_lay.addWidget(self.table_view)

        root.addWidget(table_frame, stretch=1)

        # ── Bottom Nav ──────────────────────────────────────────
        nav = QHBoxLayout()
        self.btn_back = _styled_btn("◀  Quay lại", bg="#546E7A", hover_bg="#37474F", width=120, height=40)
        self.btn_export = _styled_btn("📤  Xuất Excel", bg=C_PRIMARY, hover_bg=C_SIDEBAR_ACT, width=180, height=40, bold=True)

        nav.addWidget(self.btn_back)
        nav.addStretch()
        nav.addWidget(self.btn_export)
        root.addLayout(nav)

    def get_full_dataframe(self) -> pd.DataFrame:
        """Trả về toàn bộ DataFrame (không bị cắt) để phục vụ xuất file."""
        return self._full_df