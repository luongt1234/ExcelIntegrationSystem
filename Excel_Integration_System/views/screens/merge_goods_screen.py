"""
views/screens/merge_goods_screen.py
=====================================
Các màn hình trong flow Gộp Hàng Hóa (PyQt6):
    • GoodsStartScreen  – Chọn file + cấu hình cột
    • GoodsTabScreen    – 3-tab duyệt kết quả (Approved / Pending / Rejected)
    • GoodsFinalScreen  – Preview & xuất kết quả

Passive View:
    - KHÔNG import Controller.
    - DTO Getters trả về dict Python thuần.
    - Controller gán command cho nút.
    - Các bảng dùng QTableView + ExcelTableModel cho hiệu năng cao.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from models.excel_table_model import ExcelTableModel
from views.delegates.action_delegate import ActionDelegate
from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_SUCCESS, C_DANGER,
    C_CARD, C_BORDER, C_TEXT_MUTED, C_WARN,
    _qfont, _styled_btn,
)


def _make_table_view(parent: QWidget | None = None) -> QTableView:
    """Tạo QTableView tối ưu cho dữ liệu lớn."""
    tv = QTableView(parent)
    tv.setAlternatingRowColors(True)
    tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tv.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tv.setShowGrid(True)
    tv.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    tv.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    tv.verticalHeader().setDefaultSectionSize(32)
    tv.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    tv.verticalHeader().setVisible(False)
    tv.horizontalHeader().setStretchLastSection(True)
    tv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    tv.horizontalHeader().setHighlightSections(False)
    return tv


def _section_label(text: str, color: str = C_PRIMARY, size: int = 16) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(_qfont("Segoe UI", size, bold=True))
    lbl.setStyleSheet(f"color: {color};")
    return lbl


def _sub_label(text: str, color: str = C_TEXT_MUTED, size: int = 12) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(_qfont("Segoe UI", size))
    lbl.setStyleSheet(f"color: {color};")
    lbl.setWordWrap(True)
    return lbl


# ══════════════════════════════════════════════════════════════════════
# MÀN HÌNH 1: CHỌN FILE
# ══════════════════════════════════════════════════════════════════════
class GoodsStartScreen(QWidget):
    """
    Màn hình Gộp Hàng Hóa – Bước 1: Chọn file và cấu hình cột.

    DTO Getter:
        get_goods_config()  → dict với các key:
            input_file, input_name_col, catalog_file, catalog_col

    Controller gán:
        screen.btn_select_input.clicked.connect(ctrl.handle_select_input)
        screen.btn_select_catalog.clicked.connect(ctrl.handle_select_catalog)
        screen.btn_proceed.clicked.connect(ctrl.handle_run_matcher)
        screen.btn_back.clicked.connect(ctrl.handle_home)
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window
        self._input_file: str = ""
        self._catalog_file: str = ""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(10)

        root.addWidget(_section_label("📦  GỘP HÀNG HÓA THÔNG MINH", size=20))
        root.addWidget(_sub_label("Chuẩn hóa tên sản phẩm / hàng hóa bằng AI tương đồng  •  Tự học và sửa sai"))

        config_frame = QFrame()
        config_frame.setStyleSheet(f"background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 10px;")
        cfg_lay = QVBoxLayout(config_frame)
        cfg_lay.setContentsMargins(14, 14, 14, 14)
        cfg_lay.setSpacing(12)

        # File đầu vào
        row1 = QHBoxLayout()
        lbl_in = QLabel("📄 File Excel đầu vào:")
        lbl_in.setFont(_qfont("Segoe UI", 13, bold=True))
        row1.addWidget(lbl_in)
        self._lbl_input = QLabel("Chưa chọn file")
        self._lbl_input.setFont(_qfont("Segoe UI", 12))
        self._lbl_input.setStyleSheet(f"color: {C_TEXT_MUTED};")
        row1.addWidget(self._lbl_input)
        self.btn_select_input = _styled_btn("Chọn file", bg="#EEF2FF", fg=C_PRIMARY,
                                            hover_bg=C_BORDER, border=C_BORDER, width=100, height=30)
        row1.addWidget(self.btn_select_input)
        row1.addStretch()
        cfg_lay.addLayout(row1)

        # Cột tên hàng hóa
        row2 = QHBoxLayout()
        lbl_col1 = QLabel("Cột tên hàng hóa:")
        lbl_col1.setFont(_qfont("Segoe UI", 12))
        lbl_col1.setFixedWidth(150)
        row2.addWidget(lbl_col1)
        self.combo_name_col = QComboBox()
        self.combo_name_col.setFixedWidth(220)
        self.combo_name_col.addItem("(chọn file trước)")
        row2.addWidget(self.combo_name_col)
        row2.addStretch()
        cfg_lay.addLayout(row2)

        # Spacer
        cfg_lay.addSpacing(10)

        # File danh mục chuẩn
        row3 = QHBoxLayout()
        lbl_cat = QLabel("📋 File danh mục chuẩn:")
        lbl_cat.setFont(_qfont("Segoe UI", 13, bold=True))
        row3.addWidget(lbl_cat)
        self._lbl_catalog = QLabel("Chưa chọn file")
        self._lbl_catalog.setFont(_qfont("Segoe UI", 12))
        self._lbl_catalog.setStyleSheet(f"color: {C_TEXT_MUTED};")
        row3.addWidget(self._lbl_catalog)
        self.btn_select_catalog = _styled_btn("Chọn file", bg="#EEF2FF", fg=C_PRIMARY,
                                              hover_bg=C_BORDER, border=C_BORDER, width=100, height=30)
        row3.addWidget(self.btn_select_catalog)
        row3.addStretch()
        cfg_lay.addLayout(row3)

        # Cột tên chuẩn
        row4 = QHBoxLayout()
        lbl_col2 = QLabel("Cột tên chuẩn:")
        lbl_col2.setFont(_qfont("Segoe UI", 12))
        lbl_col2.setFixedWidth(150)
        row4.addWidget(lbl_col2)
        self.combo_catalog_col = QComboBox()
        self.combo_catalog_col.setFixedWidth(220)
        self.combo_catalog_col.addItem("(chọn file trước)")
        row4.addWidget(self.combo_catalog_col)
        row4.addStretch()
        cfg_lay.addLayout(row4)

        root.addWidget(config_frame)
        root.addStretch()

        # Nút điều hướng
        btn_row = QHBoxLayout()
        self.btn_back = _styled_btn("◀ Quay lại", bg="#546E7A", hover_bg="#37474F", height=40, width=140)
        self.btn_proceed = _styled_btn("▶ Tiếp tục: Phân tích & Xét duyệt  ➔", bg=C_ACCENT, hover_bg="#b33900",
                                       bold=True, font_size=13, height=40, width=280)
        btn_row.addWidget(self.btn_back)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_proceed)
        root.addLayout(btn_row)

    # ── Public update methods ────────────────────────────────────────
    def set_input_file(self, path: str, columns: List[str]) -> None:
        self._input_file = path
        self._lbl_input.setText(os.path.basename(path))
        self._lbl_input.setStyleSheet("color: #1565C0;")
        if columns:
            self.combo_name_col.clear()
            self.combo_name_col.addItems(columns)

    def set_catalog_file(self, path: str, columns: List[str]) -> None:
        self._catalog_file = path
        self._lbl_catalog.setText(os.path.basename(path))
        self._lbl_catalog.setStyleSheet("color: #1565C0;")
        if columns:
            self.combo_catalog_col.clear()
            self.combo_catalog_col.addItems(columns)

    # ── DTO Getter ───────────────────────────────────────────────────
    def get_goods_config(self) -> dict:
        return {
            "input_file":      self._input_file,
            "input_name_col":  self.combo_name_col.currentText(),
            "catalog_file":    self._catalog_file,
            "catalog_col":     self.combo_catalog_col.currentText(),
        }


# ══════════════════════════════════════════════════════════════════════
# MÀN HÌNH 2: 3-TAB DUYỆT KẾT QUẢ
# ══════════════════════════════════════════════════════════════════════
class GoodsTabScreen(QWidget):
    """
    Màn hình duyệt kết quả matching hàng hóa (3 tab).

    Controller gán:
        screen.btn_refresh.clicked.connect(ctrl.handle_refresh_tabs)
        screen.btn_back.clicked.connect(ctrl.handle_back_start)
        screen.btn_export.clicked.connect(ctrl.handle_show_final)
    """

    def __init__(
        self,
        window: MainWindow,
        approved_items: List[dict],
        pending_items: List[dict],
        rejected_items: List[dict],
        on_approve_fn: Callable[[str, str], None],
        on_reject_fn: Callable[[str], None],
        on_restore_fn: Callable[[str], None],
    ) -> None:
        super().__init__()
        self._window = window
        self._on_approve = on_approve_fn
        self._on_reject  = on_reject_fn
        self._on_restore = on_restore_fn
        self._build_ui(approved_items, pending_items, rejected_items)

    def _build_ui(self, approved, pending, rejected) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 15, 20, 15)
        root.setSpacing(8)

        root.addWidget(_section_label("📦  DUYỆT KẾT QUẢ GỘP HÀNG HÓA"))
        root.addWidget(_sub_label("Xem xét từng ánh xạ – bấm ĐÚNG/SAI để huấn luyện hệ thống."))

        # 3 Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {C_BORDER}; background: #FFFFFF; }}
            QTabBar::tab {{ background: #E2E8F4; color: {C_PRIMARY}; padding: 8px 16px; border: none; font-weight: bold; font-size: 12px; }}
            QTabBar::tab:selected {{ background: {C_PRIMARY}; color: #FFFFFF; }}
        """)

        tab_app = QWidget()
        tab_pen = QWidget()
        tab_rej = QWidget()

        self.tabs.addTab(tab_app, "✅  Đã học (APPROVED)")
        self.tabs.addTab(tab_pen, "⏳  Nghi ngờ (PENDING)")
        self.tabs.addTab(tab_rej, "🚫  Đã loại (REJECTED)")

        self._build_approved_tab(tab_app, approved)
        self._build_pending_tab(tab_pen, pending)
        self._build_rejected_tab(tab_rej, rejected)

        root.addWidget(self.tabs, stretch=1)

        # Nav buttons
        btn_row = QHBoxLayout()
        self.btn_back = _styled_btn("◀ Quay lại chọn file", bg="#546E7A", hover_bg="#37474F", height=38, width=180)
        self.btn_refresh = _styled_btn("🔄 Làm mới bảng", bg="#EEF2FF", fg=C_PRIMARY, hover_bg=C_BORDER, height=38, width=130)
        self.btn_export = _styled_btn("💾  Xuất kết quả  ➔", bg=C_SUCCESS, hover_bg="#1B5E20", bold=True, height=38, width=200)

        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_refresh)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_export)
        root.addLayout(btn_row)

    def _build_approved_tab(self, parent: QWidget, items: List[dict]) -> None:
        lay = QVBoxLayout(parent)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)
        lay.addWidget(QLabel(f"  {len(items)} mục đã được phê duyệt / tự học"))

        model = ExcelTableModel()
        rows = []
        for it in items:
            sim = f"{it['similarity']:.1f}%" if it.get('similarity') else "100%"
            rows.append({"Tên gốc": it["raw_name"], "→ Tên chuẩn": it["standard_name"], "Độ khớp %": sim})
        model.load_data(rows, columns=["Tên gốc", "→ Tên chuẩn", "Độ khớp %", "Hành động"])

        tv = _make_table_view()
        tv.setModel(model)
        tv.horizontalHeader().resizeSection(0, 300)
        tv.horizontalHeader().resizeSection(1, 300)
        tv.horizontalHeader().resizeSection(2, 100)

        # Action delegate
        delegate = ActionDelegate(button_labels=["✖ SAI (Loại)"], button_presets=["reject"], button_width=100)
        def on_action(row, btn_idx):
            data = model.get_row_data(row)
            self._on_reject(data["Tên gốc"])
            # Remove row from view
            del model._data[row]
            model.layoutChanged.emit()
            lay.itemAt(0).widget().setText(f"  {len(model._data)} mục đã được phê duyệt / tự học")

        delegate.btn_clicked.connect(on_action)
        tv.setItemDelegateForColumn(3, delegate)
        lay.addWidget(tv, stretch=1)

    def _build_pending_tab(self, parent: QWidget, items: List[dict]) -> None:
        lay = QVBoxLayout(parent)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)
        lay.addWidget(QLabel(f"  {len(items)} mục đang chờ xét duyệt"))

        model = ExcelTableModel()
        rows = []
        for it in items:
            sim = f"{it['similarity']:.1f}%" if it.get('similarity') else "?"
            rows.append({"Tên gốc": it["raw_name"], "Đề xuất ghép": it.get("standard_name") or "(không gợi ý)", "Độ khớp %": sim})
        model.load_data(rows, columns=["Tên gốc", "Đề xuất ghép", "Độ khớp %", "Hành động"])

        tv = _make_table_view()
        tv.setModel(model)
        tv.horizontalHeader().resizeSection(0, 300)
        tv.horizontalHeader().resizeSection(1, 300)
        tv.horizontalHeader().resizeSection(2, 100)

        delegate = ActionDelegate(button_labels=["✔ ĐÚNG", "✖ SAI"], button_presets=["approve", "reject"], button_width=80)
        def on_action(row, btn_idx):
            data = model.get_row_data(row)
            raw = data["Tên gốc"]
            if btn_idx == 0:
                std = data["Đề xuất ghép"]
                if std == "(không gợi ý)": std = ""
                self._on_approve(raw, std)
            else:
                self._on_reject(raw)
            del model._data[row]
            model.layoutChanged.emit()
            lay.itemAt(0).widget().setText(f"  {len(model._data)} mục đang chờ xét duyệt")

        delegate.btn_clicked.connect(on_action)
        tv.setItemDelegateForColumn(3, delegate)
        lay.addWidget(tv, stretch=1)

    def _build_rejected_tab(self, parent: QWidget, items: List[dict]) -> None:
        lay = QVBoxLayout(parent)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)
        lay.addWidget(QLabel(f"  {len(items)} mục trong blacklist – sẽ KHÔNG bị gộp"))

        model = ExcelTableModel()
        rows = []
        for it in items:
            rows.append({"Tên gốc": it["raw_name"], "Tên chuẩn cũ (nếu có)": it.get("standard_name") or ""})
        model.load_data(rows, columns=["Tên gốc", "Tên chuẩn cũ (nếu có)", "Hành động"])

        tv = _make_table_view()
        tv.setModel(model)
        tv.horizontalHeader().resizeSection(0, 350)
        tv.horizontalHeader().resizeSection(1, 350)

        delegate = ActionDelegate(button_labels=["↩ Khôi phục"], button_presets=["restore"], button_width=120)
        def on_action(row, btn_idx):
            data = model.get_row_data(row)
            self._on_restore(data["Tên gốc"])
            del model._data[row]
            model.layoutChanged.emit()
            lay.itemAt(0).widget().setText(f"  {len(model._data)} mục trong blacklist – sẽ KHÔNG bị gộp")

        delegate.btn_clicked.connect(on_action)
        tv.setItemDelegateForColumn(2, delegate)
        lay.addWidget(tv, stretch=1)


# ══════════════════════════════════════════════════════════════════════
# MÀN HÌNH 3: KẾT QUẢ & XUẤT
# ══════════════════════════════════════════════════════════════════════
class GoodsFinalScreen(QWidget):
    """
    Màn hình kết quả gộp hàng hóa.

    Controller gán:
        screen.btn_export.clicked.connect(ctrl.handle_export_goods)
        screen.btn_review.clicked.connect(ctrl.handle_back_review)
        screen.btn_home.clicked.connect(ctrl.handle_home)
    """

    def __init__(
        self,
        window: MainWindow,
        result_df,
        n_approved: int,
        n_pending: int,
        n_rejected: int,
    ) -> None:
        super().__init__()
        self._window = window
        self._build_ui(result_df, n_approved, n_pending, n_rejected)

    def _build_ui(self, df, n_approved, n_pending, n_rejected) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 15, 20, 15)
        root.setSpacing(10)

        root.addWidget(_section_label("📦  KẾT QUẢ GỘP HÀNG HÓA"))

        # Summary cards
        summary = QHBoxLayout()
        for label, value, color in [
            ("✅ Đã duyệt (APPROVED)", str(n_approved), C_SUCCESS),
            ("⏳ Còn chờ (PENDING)",   str(n_pending),  C_WARN),
            ("🚫 Đã loại (REJECTED)",  str(n_rejected), C_DANGER),
        ]:
            card = QFrame()
            card.setFixedSize(200, 70)
            card.setStyleSheet(f"background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 10px;")
            cl = QVBoxLayout(card)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_l = QLabel(label)
            lbl_l.setFont(_qfont("Segoe UI", 12))
            lbl_l.setStyleSheet(f"color: {C_TEXT_MUTED};")
            lbl_v = QLabel(value)
            lbl_v.setFont(_qfont("Segoe UI", 22, bold=True))
            lbl_v.setStyleSheet(f"color: {color};")
            cl.addWidget(lbl_l, alignment=Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(lbl_v, alignment=Qt.AlignmentFlag.AlignCenter)
            summary.addWidget(card)
        summary.addStretch()
        root.addLayout(summary)

        # Preview table
        self._model = ExcelTableModel()
        if df is not None and not df.empty:
            self._model.load_data(df)
        self._table = _make_table_view()
        self._table.setModel(self._model)
        root.addWidget(self._table, stretch=1)

        if df is not None:
            root.addWidget(_sub_label(f"(Hiển thị đầy đủ {len(df)} dòng – file xuất chứa đầy đủ.)"))

        # Nút điều hướng
        btn_row = QHBoxLayout()
        self.btn_export = _styled_btn("💾  XUẤT FILE EXCEL", bg=C_SUCCESS, hover_bg="#1B5E20", bold=True, font_size=14, height=46, width=220)
        self.btn_review = _styled_btn("🔄  Tiếp tục duyệt", bg="#1565C0", hover_bg="#0D47A1", height=46, width=180)
        self.btn_home = _styled_btn("🏠  Về trang chủ", bg="#546E7A", hover_bg="#37474F", height=46, width=160)

        btn_row.addWidget(self.btn_export)
        btn_row.addWidget(self.btn_review)
        btn_row.addWidget(self.btn_home)
        btn_row.addStretch()
        root.addLayout(btn_row)
