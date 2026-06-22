"""
views/delegates/action_delegate.py
=====================================
ActionDelegate – QStyledItemDelegate vẽ nút hành động bằng QPainter.

KIẾN TRÚC MODEL/VIEW/DELEGATE – Nguyên tắc bất biến:
    ✅ ĐÚNG : Ghi đè paint() → dùng QPainter VẼ hình ảnh nút lên canvas.
    ✅ ĐÚNG : Ghi đè editorEvent() → tính tọa độ click, emit Signal.
    ❌ SAI  : Tạo QPushButton / QWidget trong paint() hoặc trong ô bảng.

Lý do:
    Mỗi QPushButton tạo ra = 1 object Python + 1 Qt C++ object + paint overhead.
    Với 100.000 hàng → 100.000 nút → RAM cực lớn, UI đứng máy.
    QPainter chỉ VẼ pixel, không tạo object → O(1) bộ nhớ dù triệu dòng.
"""

from __future__ import annotations

from PyQt6.QtCore import (
    QEvent,
    QModelIndex,
    QObject,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)


class ActionDelegate(QStyledItemDelegate):
    """
    Delegate vẽ các nút hành động vào cột chỉ định.

    Cách dùng:
        delegate = ActionDelegate(columns={2: ["✔ Duyệt", "✖ Loại"]})
        table_view.setItemDelegateForColumn(2, delegate)

        delegate.btn_clicked.connect(lambda row, btn_idx: ...)

    Signals:
        btn_clicked(row: int, btn_idx: int)
            btn_idx = 0, 1, 2, ... tương ứng với index trong danh sách label.
    """

    # Signal phát ra khi user click một nút trong ô delegate
    # row: int – chỉ số hàng; btn_idx: int – chỉ số nút (0-based)
    btn_clicked = pyqtSignal(int, int)

    # ── Cấu hình hiển thị nút ────────────────────────────────────────
    _BTN_HEIGHT   = 26   # px chiều cao nút
    _BTN_PADDING  = 4    # px padding trái/phải trong nút
    _BTN_SPACING  = 6    # px khoảng cách giữa 2 nút
    _ROW_PADDING  = 3    # px padding trên/dưới trong ô

    # Bảng màu preset cho từng loại nút
    _PRESET_COLORS = {
        "approve":  ("#2E7D32", "#1B5E20", "#FFFFFF"),  # xanh lá
        "reject":   ("#C62828", "#B71C1C", "#FFFFFF"),  # đỏ
        "restore":  ("#1565C0", "#0D47A1", "#FFFFFF"),  # xanh dương
        "view":     ("#1976D2", "#1565C0", "#FFFFFF"),  # xanh nhạt
        "neutral":  ("#546E7A", "#37474F", "#FFFFFF"),  # xám
    }

    def __init__(
        self,
        button_labels: list[str] | None = None,
        button_presets: list[str] | None = None,
        button_width: int = 72,
        parent: QObject | None = None,
    ) -> None:
        """
        Args:
            button_labels  : Danh sách nhãn nút, VD: ["✔ Duyệt", "✖ Loại"]
            button_presets : Tên preset màu tương ứng, VD: ["approve", "reject"]
                             Nếu None → dùng "neutral" cho tất cả.
            button_width   : Chiều rộng mỗi nút (pixel).
            parent         : QObject cha.
        """
        super().__init__(parent)
        self._labels   = button_labels  or ["Xem", "Xóa"]
        self._presets  = button_presets or ["view", "reject"]
        self._btn_w    = button_width
        # Đảm bảo số preset khớp với số nhãn
        while len(self._presets) < len(self._labels):
            self._presets.append("neutral")

    # ==================================================================
    # OVERRIDE: paint() – VẼ hình ảnh nút bằng QPainter
    # ==================================================================
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """
        Qt gọi hàm này để vẽ NỘI DUNG của ô.
        Ta dùng QPainter để VẼ hình chữ nhật bo góc + text.

        KHÔNG tạo QPushButton hay bất kỳ QWidget nào ở đây!
        """
        if not index.isValid():
            super().paint(painter, option, index)
            return

        painter.save()

        # Vẽ nền ô (selected / alternating)
        self._draw_cell_background(painter, option)

        # Tính tọa độ các nút
        rects = self._calc_button_rects(option.rect)

        for i, (rect, label, preset) in enumerate(
            zip(rects, self._labels, self._presets)
        ):
            self._draw_button(painter, rect, label, preset)

        painter.restore()

    def _draw_cell_background(
        self, painter: QPainter, option: QStyleOptionViewItem
    ) -> None:
        """Vẽ nền ô (màu selected hoặc alternating row color)."""
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#DBEAFE"))
        else:
            # Lấy màu nền từ model (BackgroundRole)
            bg = option.backgroundBrush
            if bg.style() != Qt.BrushStyle.NoBrush:
                painter.fillRect(option.rect, bg)
            else:
                painter.fillRect(option.rect, QColor("#FFFFFF"))

    def _draw_button(
        self,
        painter: QPainter,
        rect: QRect,
        label: str,
        preset: str,
    ) -> None:
        """
        Vẽ một nút tại vị trí rect.
        Sử dụng bo góc 4px để trông hiện đại.
        """
        bg_color, _, text_color = self._PRESET_COLORS.get(
            preset, self._PRESET_COLORS["neutral"]
        )

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Vẽ nền nút
        painter.setBrush(QBrush(QColor(bg_color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4.0, 4.0)

        # Vẽ chữ trên nút
        painter.setPen(QPen(QColor(text_color)))
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _calc_button_rects(self, cell_rect: QRect) -> list[QRect]:
        """
        Tính tọa độ từng nút trong ô, căn giữa theo chiều dọc & ngang.
        """
        n = len(self._labels)
        total_w = (self._btn_w * n) + (self._BTN_SPACING * (n - 1))
        start_x = cell_rect.left() + (cell_rect.width() - total_w) // 2
        btn_y   = cell_rect.top() + (cell_rect.height() - self._BTN_HEIGHT) // 2

        rects = []
        x = start_x
        for _ in range(n):
            rects.append(QRect(x, btn_y, self._btn_w, self._BTN_HEIGHT))
            x += self._btn_w + self._BTN_SPACING
        return rects

    # ==================================================================
    # OVERRIDE: editorEvent() – XỬ LÝ CLICK CHUỘT
    # ==================================================================
    def editorEvent(
        self,
        event: QEvent,
        model,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        """
        Qt gọi hàm này khi có sự kiện chuột trên ô.
        Ta tính xem click trúng nút nào, rồi emit Signal tương ứng.

        Trả về True nếu đã xử lý event (ngăn Qt xử lý tiếp).
        """
        if not index.isValid():
            return False

        # Chỉ quan tâm sự kiện nhả chuột trái (tránh kích hoạt khi kéo)
        if event.type() != QEvent.Type.MouseButtonRelease:
            return False
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        rects = self._calc_button_rects(option.rect)
        pos   = event.pos()

        for btn_idx, rect in enumerate(rects):
            if rect.contains(pos):
                # Emit signal – Qt sẽ route về main thread tự động
                self.btn_clicked.emit(index.row(), btn_idx)
                return True  # Event đã được xử lý

        return False

    # ==================================================================
    # OVERRIDE: sizeHint() – GỢI Ý KÍCH THƯỚC Ô
    # ==================================================================
    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QSize:
        """Chiều cao tối thiểu cho hàng chứa nút."""
        return QSize(
            self._btn_w * len(self._labels)
            + self._BTN_SPACING * (len(self._labels) - 1)
            + 24,  # padding ngang
            self._BTN_HEIGHT + self._ROW_PADDING * 2,
        )
