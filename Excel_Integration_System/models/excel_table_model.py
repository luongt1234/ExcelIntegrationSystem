"""
models/excel_table_model.py
============================
ExcelTableModel – QAbstractTableModel chung cho toàn hệ thống.

Kiến trúc Model/View của Qt:
    • Model giữ THAM CHIẾU đến dữ liệu (DataFrame hoặc list[dict]).
      KHÔNG copy dữ liệu vào widget.
    • View (QTableView) chỉ gọi data() khi CẦN HIỂN THỊ ô đó (virtual scrolling).
    • Delegate (QStyledItemDelegate) chịu trách nhiệm vẽ các ô đặc biệt.

Điều này cho phép bảng xử lý hàng triệu dòng mà không tốn RAM:
    - RAM = kích thước dữ liệu thực, KHÔNG phải số widget vật lý.
    - Tốc độ scroll = O(1), không phụ thuộc vào số dòng.
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

import pandas as pd

from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont


# ── Hằng màu chung (khớp với màu trong main_window.py) ───────────────
_COLOR_ROW_ODD     = QColor("#F4F8FC")
_COLOR_ROW_EVEN    = QColor("#FFFFFF")
_COLOR_HEADER_BG   = QColor("#1B3A6B")
_COLOR_HEADER_FG   = QColor("#FFFFFF")
_COLOR_SELECTED_BG = QColor("#DBEAFE")
_COLOR_SELECTED_FG = QColor("#1B3A6B")
_COLOR_TEXT        = QColor("#1A202C")


class ExcelTableModel(QAbstractTableModel):
    """
    Model bảng dữ liệu tổng quát – nhận đầu vào là:
        • pd.DataFrame
        • list[dict]  (mỗi dict là một hàng)

    Sử dụng:
        model = ExcelTableModel()
        model.load_data(df)          # nạp DataFrame
        table_view.setModel(model)   # gắn vào View

    Thread-Safety:
        Gọi load_data() / clear() từ main thread.
        Nếu gọi từ worker thread → dùng QMetaObject.invokeMethod hoặc
        emit signal rồi connect về slot trong main thread.
    """

    # Signal phát ra khi dữ liệu thay đổi (controllers có thể connect)
    data_changed_signal = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # _data: list of lists (rows) – được tạo từ DataFrame một lần khi load
        self._data: List[List[Any]] = []
        # _headers: list tên cột
        self._headers: List[str] = []
        # _df_ref: giữ tham chiếu DataFrame gốc để controller truy cập nếu cần
        self._df_ref: Optional[pd.DataFrame] = None

    # ==================================================================
    # PUBLIC API
    # ==================================================================
    def load_data(
        self,
        source: Union[pd.DataFrame, List[dict], None],
        columns: Optional[List[str]] = None,
    ) -> None:
        """
        Nạp dữ liệu mới vào model.

        Args:
            source  : DataFrame, list[dict], hoặc None (clear).
            columns : Danh sách cột muốn hiển thị (None = tất cả cột).
        """
        self.beginResetModel()
        try:
            if source is None or (isinstance(source, pd.DataFrame) and source.empty):
                self._data = []
                self._headers = columns or []
                self._df_ref = None
                return

            if isinstance(source, pd.DataFrame):
                self._df_ref = source
                if columns:
                    # Chỉ lấy cột có trong DataFrame
                    cols = [c for c in columns if c in source.columns]
                else:
                    cols = list(source.columns)
                self._headers = cols
                # Chuyển sang list[list] – thao tác O(N) chỉ chạy 1 lần khi load
                # fillna("") để tránh hiển thị "nan" trên UI
                df_view = source[cols].fillna("").astype(str)
                self._data = df_view.values.tolist()

            elif isinstance(source, list):
                self._df_ref = None
                if not source:
                    self._data = []
                    self._headers = columns or []
                    return
                if columns:
                    self._headers = columns
                else:
                    # Lấy union tất cả key từ list of dicts
                    seen: dict = {}
                    for row in source:
                        for k in row:
                            seen[k] = None
                    self._headers = list(seen.keys())
                # Build data matrix
                self._data = [
                    [str(row.get(h, "")) for h in self._headers]
                    for row in source
                ]
        finally:
            self.endResetModel()
            self.data_changed_signal.emit()

    def clear(self) -> None:
        """Xóa toàn bộ dữ liệu."""
        self.load_data(None)

    def get_row_data(self, row: int) -> dict:
        """Trả về dict dữ liệu của hàng row (để controller xử lý)."""
        if 0 <= row < len(self._data):
            return dict(zip(self._headers, self._data[row]))
        return {}

    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """Trả về DataFrame gốc (nếu load từ DataFrame)."""
        return self._df_ref

    # ==================================================================
    # QAbstractTableModel – PHẢI implement đủ 5 hàm sau
    # ==================================================================
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Trả về số hàng.
        Qt gọi hàm này mỗi khi cần biết kích thước model.
        """
        if parent.isValid():
            return 0  # Không có child rows (flat model)
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Trả về số cột."""
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Trả về dữ liệu cho một ô cụ thể.

        Qt chỉ gọi hàm này khi ô đó NẰM TRONG VÙNG NHÌN THẤY (viewport).
        Đây là cơ chế "virtual scrolling" giúp bảng siêu nhẹ.

        Các role quan trọng:
            DisplayRole   – văn bản hiển thị
            BackgroundRole – màu nền hàng (zebra striping)
            ForegroundRole – màu chữ
            TextAlignmentRole – căn lề
            UserRole      – dữ liệu thô (dict) cho controller dùng
        """
        if not index.isValid():
            return None

        row, col = index.row(), index.column()

        # Guard: tránh IndexError khi model đang reset
        if row >= len(self._data) or col >= len(self._headers):
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            # Trả về giá trị dạng string để hiển thị
            return self._data[row][col]

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Zebra striping: hàng chẵn/lẻ xen kẽ màu
            return _COLOR_ROW_ODD if row % 2 == 0 else _COLOR_ROW_EVEN

        elif role == Qt.ItemDataRole.ForegroundRole:
            return _COLOR_TEXT

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Căn giữa cho cột số/ngày; căn trái cho text
            header = self._headers[col] if col < len(self._headers) else ""
            center_cols = {"STT", "Ngày Sinh", "Ngày nộp", "Số CCCD/ID", "Tình trạng"}
            if header in center_cols:
                return int(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
            return int(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

        elif role == Qt.ItemDataRole.UserRole:
            # Trả về toàn bộ dữ liệu hàng dạng dict cho Delegate / Controller
            return self.get_row_data(row)

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """
        Trả về tiêu đề cột (horizontal) hoặc số thứ tự hàng (vertical).
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._headers):
                    return self._headers[section]
            else:
                # Vertical header: số thứ tự hàng (1-indexed)
                return str(section + 1)

        elif role == Qt.ItemDataRole.FontRole:
            if orientation == Qt.Orientation.Horizontal:
                font = QFont("Segoe UI", 10)
                font.setBold(True)
                return font

        elif role == Qt.ItemDataRole.BackgroundRole:
            if orientation == Qt.Orientation.Horizontal:
                return _COLOR_HEADER_BG

        elif role == Qt.ItemDataRole.ForegroundRole:
            if orientation == Qt.Orientation.Horizontal:
                return _COLOR_HEADER_FG

        return None
