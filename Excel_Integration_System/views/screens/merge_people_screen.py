"""
views/screens/merge_people_screen.py
=====================================
Tập hợp các màn hình trong flow Gộp hồ sơ người (PyQt6):
    • StructureConfirmScreen  – Bước 0: Xác nhận cấu trúc từng file
    • DedupConfigScreen       – Bước 1: Chọn khóa quét trùng
    • ReviewScreen            – Bước 2: Duyệt từng cặp trùng
    • FinalScreen             – Kết quả & xuất file
    • LeftJoinKeyScreen       – Chế độ 2: Cấu hình cặp khóa
    • LeftJoinResultScreen    – Chế độ 2: Kết quả

Nguyên tắc:
    - View KHÔNG import Controller.
    - Tất cả trạng thái nội bộ được che sau DTO Getter.
    - Cập nhật UI từ thread nền phải qua QTimer.singleShot(0, cb) ở Controller.
    - Bảng dữ liệu dùng QTableView + ExcelTableModel (KHÔNG dùng QTableWidget).
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from models.excel_table_model import ExcelTableModel
from views.delegates.action_delegate import ActionDelegate
from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_SUCCESS, C_DANGER,
    C_WARN, C_CARD, C_BORDER, C_BG_LIGHT, C_TEXT_MUTED, C_SIDEBAR_ACT,
    _qfont, _styled_btn,
)

# Cột chuẩn toàn hệ thống
STANDARD_COLUMNS = [
    "Họ và Tên", "Ngày Sinh", "Số CCCD/ID",
    "Số Điện Thoại", "Email", "Địa Chỉ",
    "Vị trí", "Đơn vị", "Ngày nộp",
    "Tình trạng", "Văn bằng", "Ghi Chú",
]


def _make_table_view(parent: QWidget | None = None) -> QTableView:
    """
    Helper: tạo QTableView cấu hình tối ưu dùng chung.

    Các tối ưu:
        ScrollPerPixel  – cuộn mượt thay vì nhảy theo hàng
        setUniformRowHeights – Qt không cần đo từng hàng → tăng tốc render
        setWordWrap(False)   – tắt word wrap để render nhanh hơn
    """
    tv = QTableView(parent)
    tv.setAlternatingRowColors(True)
    tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tv.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tv.setShowGrid(True)
    # Cuộn mượt pixel-by-pixel
    tv.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    tv.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    # Tối ưu render: chiều cao hàng đồng đều
    tv.verticalHeader().setDefaultSectionSize(32)
    tv.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    tv.verticalHeader().setVisible(False)
    # Header ngang
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


def _info_box(text: str, bg: str = "#E3F2FD", fg: str = "#1565C0") -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(f"background: {bg}; border-radius: 6px; border: none;")
    lay = QHBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    lbl = QLabel(text)
    lbl.setFont(_qfont("Segoe UI", 11))
    lbl.setStyleSheet(f"color: {fg}; background: transparent;")
    lbl.setWordWrap(True)
    lay.addWidget(lbl)
    return frame


# ══════════════════════════════════════════════════════════════════════
# BƯỚC 0: XÁC NHẬN CẤU TRÚC TỪNG FILE
# ══════════════════════════════════════════════════════════════════════
class StructureConfirmScreen(QWidget):
    """
    Màn hình Bước 0: Xác nhận cấu trúc từng file.

    DTO Getters:
        get_file_structures()  → Dict[str, dict]
        is_all_confirmed()     → bool

    Controller gán:
        screen.btn_next.clicked.connect(ctrl.handle_go_dedup)
        screen.btn_back.clicked.connect(ctrl.handle_back_home)
        screen.btn_home.clicked.connect(ctrl.handle_home)
    """

    def __init__(
        self,
        window: MainWindow,
        file_paths: List[str],
        scan_results: Dict[str, dict],
        saved_profiles: Dict[str, Optional[dict]],
        merge_mode: int = 1,
        pre_confirmed_structures: Optional[Dict[str, dict]] = None,
        rescan_callback=None,
    ) -> None:
        super().__init__()
        self._window = window
        self._file_paths = file_paths
        self._scan_results = scan_results
        self._saved_profiles = saved_profiles
        self._merge_mode = merge_mode
        self._rescan_callback = rescan_callback

        self._file_structures: Dict[str, dict] = (
            dict(pre_confirmed_structures) if pre_confirmed_structures else {}
        )
        self._struct_panels: Dict[str, dict] = {}

        self._build_ui()
        self._restore_confirmed_state()

    def _restore_confirmed_state(self) -> None:
        for path, _ in self._file_structures.items():
            refs = self._struct_panels.get(path, {})
            if "lbl_confirm_status" in refs:
                refs["lbl_confirm_status"].setText("✅ Đã xác nhận (khôi phục)")
                refs["lbl_confirm_status"].setStyleSheet("color: #2E7D32;")
        if self.is_all_confirmed():
            self.btn_next.setEnabled(True)
            self.lbl_struct_status.setText(
                f"✅ Tất cả {len(self._file_paths)} file đã xác nhận"
            )
            self.lbl_struct_status.setStyleSheet("color: #2E7D32;")

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 6)
        root.setSpacing(6)

        # ── Thanh tiến trình bước ────────────────────────────────────
        step_bar = QFrame()
        step_bar.setStyleSheet("background: #EEF2FF; border-radius: 8px;")
        step_lay = QHBoxLayout(step_bar)
        step_lay.setContentsMargins(16, 6, 16, 6)
        for label, active in [
            ("① Xác nhận cấu trúc file", True),
            ("② Cấu hình cặp khóa ghép", False),
            ("③ Chạy gộp & xuất kết quả", False),
        ]:
            lbl = QLabel(label)
            lbl.setFont(_qfont("Segoe UI", 12, bold=active))
            lbl.setStyleSheet(f"color: {'#1565C0' if active else '#9E9E9E'}; background: transparent;")
            step_lay.addWidget(lbl)
            step_lay.addSpacing(16)
        step_lay.addStretch()
        root.addWidget(step_bar)

        # ── Header ───────────────────────────────────────────────────
        root.addWidget(_section_label("BƯỚC 1 / 3  –  XÁC NHẬN CẤU TRÚC TỪNG FILE"))
        root.addWidget(_info_box(
            "🔍  Ứng dụng đã tự động nhận diện cấu trúc file Excel của bạn.\n"
            "     Hãy kiểm tra: (1) Sheet đúng chưa?  "
            "(2) Dòng tiêu đề (Header) đúng chưa?  "
            "(3) Các cột có được ánh xạ hợp lý không?\n"
            "     Sau khi kiểm tra xong, bấm  ✔ Xác nhận  cho từng file, rồi bấm Tiếp theo."
        ))

        # ── Scroll area chứa các file panel ─────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        grid = QGridLayout(scroll_content)
        grid.setSpacing(8)

        n_files = len(self._file_paths)
        for fi, fpath in enumerate(self._file_paths):
            panel = self._build_file_panel(
                fpath,
                self._scan_results.get(fpath, {}),
                self._saved_profiles.get(fpath),
            )
            col = fi % 2
            row = fi // 2
            grid.addWidget(panel, row, col)
            if n_files == 1:
                grid.setColumnStretch(0, 1)
                grid.setColumnStretch(1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        scroll.setWidget(scroll_content)
        root.addWidget(scroll, stretch=1)

        # ── Bottom nav ───────────────────────────────────────────────
        nav = QHBoxLayout()
        nav.setContentsMargins(4, 4, 4, 4)

        self.btn_back = _styled_btn(
            "◀  Quay lại chọn file",
            bg="#546E7A", hover_bg="#37474F",
            width=180, height=40,
        )
        self.btn_home = _styled_btn(
            "🏠  Trang chủ",
            bg="transparent", fg=C_PRIMARY, hover_bg=C_BORDER,
            border=C_BORDER, width=140, height=40,
        )

        next_label = (
            "Tiếp theo: Cấu hình Gộp Chọn Lọc  ➔"
            if self._merge_mode == 2
            else "Tiếp theo: Chọn khóa quét trùng  ➔"
        )
        self.btn_next = _styled_btn(
            next_label,
            bg=C_ACCENT, hover_bg="#b33900",
            width=300, height=40, bold=True, font_size=13,
        )
        self.btn_next.setEnabled(False)

        self.lbl_struct_status = QLabel("")
        self.lbl_struct_status.setFont(_qfont("Segoe UI", 12))
        self.lbl_struct_status.setStyleSheet(f"color: {C_TEXT_MUTED};")

        nav.addWidget(self.btn_back)
        nav.addWidget(self.btn_home)
        nav.addStretch()
        nav.addWidget(self.lbl_struct_status)
        nav.addWidget(self.btn_next)

        root.addLayout(nav)

    def _build_file_panel(
        self, path: str, scan: dict, saved_profile: Optional[dict]
    ) -> QFrame:
        """Tạo panel xác nhận cấu trúc cho 1 file."""
        fname = os.path.basename(path)
        active_profile = self._file_structures.get(path) or saved_profile

        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        # Row 1: Title, Buttons & Confidence
        conf = scan.get("confidence_score", 0.0)
        conf_color = "#2E7D32" if conf >= 0.5 else "#E65100"
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        
        lbl_fname = QLabel(f"📄  {fname}")
        lbl_fname.setFont(_qfont("Segoe UI", 12, bold=True))
        lbl_fname.setStyleSheet("color: #1565C0; background: transparent;")
        
        lbl_conf = QLabel(f"Độ tin cậy: {int(conf * 100)}%")
        lbl_conf.setFont(_qfont("Segoe UI", 10, bold=True))
        lbl_conf.setStyleSheet(f"color: {conf_color}; background: transparent;")
        
        btn_open = _styled_btn("👁 Xem file", bg="#E3F2FD", fg="#1565C0", hover_bg="#BBDEFB",
                               border="#90CAF9", width=90, height=26, font_size=10)
        btn_open.clicked.connect(lambda: self._open_file(path))

        btn_rescan = _styled_btn("🔍 Dò lại", bg="#F5F5F5", fg=C_PRIMARY, hover_bg=C_BORDER,
                                  border=C_BORDER, width=80, height=26, font_size=10)
        
        title_row.addWidget(lbl_fname)
        title_row.addStretch()
        title_row.addWidget(btn_open)
        title_row.addWidget(btn_rescan)
        title_row.addWidget(lbl_conf)
        lay.addLayout(title_row)

        # Row 2: Sheet & Header settings
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(8)
        
        row1.addWidget(QLabel("Sheet:"))
        sheet_names = scan.get("sheet_names") or ["Sheet1"]
        sheet_combo = QComboBox()
        sheet_combo.setFixedWidth(140)
        sheet_combo.addItems(sheet_names)
        if active_profile and active_profile.get("sheet_name") in sheet_names:
            sheet_combo.setCurrentText(active_profile["sheet_name"])
        else:
            selected = scan.get("selected_sheet") or sheet_names[0]
            if selected in sheet_names:
                sheet_combo.setCurrentText(selected)
        row1.addWidget(sheet_combo)

        row1.addWidget(QLabel("   Dòng header (0-based):"))
        if active_profile and "header_row" in active_profile:
            hval = str(active_profile["header_row"])
        else:
            hval = str(scan.get("suggested_header_row", 0))
        header_entry = QLineEdit(hval)
        header_entry.setFixedWidth(40)
        row1.addWidget(header_entry)

        hs = int(scan.get("header_start_row", scan.get("suggested_header_row", 0)))
        he = int(scan.get("header_end_row", hs))
        ds = int(scan.get("data_start_row", hs + 1))
        lbl_multi = QLabel(
            f" (Header: dòng {hs+1}-{he+1} · Dữ liệu: dòng {ds+1})"
        )
        lbl_multi.setFont(_qfont("Segoe UI", 10))
        lbl_multi.setStyleSheet("color: #1565C0; background: transparent;")
        row1.addWidget(lbl_multi)
        
        row1.addStretch()
        lay.addLayout(row1)

        # Column table scroll area
        col_scroll = QScrollArea()
        col_scroll.setMinimumHeight(220)
        col_scroll.setWidgetResizable(True)
        col_scroll.setFrameShape(QFrame.Shape.NoFrame)
        col_scroll.setStyleSheet("background: transparent;")

        col_container = QWidget()
        col_container.setStyleSheet("background: transparent;")
        col_lay = QVBoxLayout(col_container)
        col_lay.setSpacing(2)
        col_lay.setContentsMargins(0, 0, 0, 0)
        col_scroll.setWidget(col_container)

        # Lưu tham chiếu widgets để build_col_rows() dùng
        col_checkboxes: Dict[str, QCheckBox] = {}
        col_combos: Dict[str, QComboBox] = {}

        # Quick-select buttons
        qs_row = QHBoxLayout()
        btn_all = _styled_btn("✅ Chọn tất cả", bg="#E8F5E9", fg=C_SUCCESS, hover_bg="#C8E6C9",
                               border=C_SUCCESS, width=120, height=24, font_size=11)
        btn_none = _styled_btn("☐ Bỏ chọn tất cả", bg="#ECEFF1", fg=C_TEXT_MUTED,
                                hover_bg="#E0E0E0", border=C_BORDER, width=130, height=24, font_size=11)
        btn_all.clicked.connect(lambda: [cb.setChecked(True) for cb in col_checkboxes.values()])
        btn_none.clicked.connect(lambda: [cb.setChecked(False) for cb in col_checkboxes.values()])
        qs_row.addWidget(btn_all)
        qs_row.addWidget(btn_none)
        qs_row.addStretch()
        col_lay.addLayout(qs_row)

        # Header hàng cột
        hdr_row = QHBoxLayout()
        for lbl_text, w in [("Giữ", 40), ("Tên cột gốc", 200), ("→ Ánh xạ sang", 200)]:
            lbl = QLabel(lbl_text)
            lbl.setFont(_qfont("Segoe UI", 11, bold=True))
            lbl.setFixedWidth(w)
            hdr_row.addWidget(lbl)
        hdr_row.addStretch()
        col_lay.addLayout(hdr_row)

        def build_col_rows(detected_cols, suggested_mapping, _saved=None):
            """Xây dựng lại danh sách hàng cột trong panel."""
            # Xóa các widget cũ (giữ lại quick-select và header)
            while col_lay.count() > 2:
                item = col_lay.takeAt(2)
                if item.widget():
                    item.widget().deleteLater()

            col_checkboxes.clear()
            col_combos.clear()

            if not detected_cols:
                lbl_empty = QLabel("Không có cột nào được phát hiện.")
                lbl_empty.setStyleSheet(f"color: {C_TEXT_MUTED};")
                col_lay.addWidget(lbl_empty)
                return

            saved_selected = set(_saved.get("selected_columns", [])) if _saved else None
            saved_map = _saved.get("column_mapping", {}) if _saved else {}

            for col in detected_cols:
                row_w = QWidget()
                row_w.setFixedHeight(34)
                row_w.setStyleSheet("background: transparent;")
                row_lay = QHBoxLayout(row_w)
                row_lay.setContentsMargins(0, 2, 0, 2)
                row_lay.setSpacing(4)

                checked = (col in saved_selected) if saved_selected is not None else True
                cb = QCheckBox()
                cb.setChecked(checked)
                cb.setFixedWidth(40)
                row_lay.addWidget(cb)

                col_entry = QLineEdit(col)
                col_entry.setReadOnly(True)
                col_entry.setFixedWidth(200)
                col_entry.setStyleSheet("background: transparent; border: none; font-size: 11px;")
                row_lay.addWidget(col_entry)

                mapping_combo = QComboBox()
                mapping_combo.setEditable(True)
                mapping_combo.setFixedWidth(200)
                mapping_combo.addItems(["Bỏ qua (Ignore)"] + STANDARD_COLUMNS)
                combo_val = (
                    saved_map.get(col, suggested_mapping.get(col, "Bỏ qua (Ignore)"))
                    if saved_selected is not None
                    else suggested_mapping.get(col, "Bỏ qua (Ignore)")
                )
                if combo_val:
                    mapping_combo.setCurrentText(combo_val)
                row_lay.addWidget(mapping_combo)
                row_lay.addStretch()

                col_lay.addWidget(row_w)
                col_checkboxes[col] = cb
                col_combos[col] = mapping_combo

        # Build lần đầu
        build_col_rows(
            scan.get("detected_columns", []),
            scan.get("suggested_mapping", {}),
            _saved=active_profile,
        )
        lay.addWidget(col_scroll)

        # Action row: status + nút xác nhận
        action_row = QHBoxLayout()
        lbl_status = QLabel("⬜ Chưa xác nhận")
        lbl_status.setFont(_qfont("Segoe UI", 12))
        lbl_status.setStyleSheet(f"color: {C_TEXT_MUTED}; background: transparent;")

        btn_confirm = _styled_btn(
            "✔ Xác nhận cấu trúc file này",
            bg="#1565C0", hover_bg="#0D47A1",
            width=220, height=30, font_size=11,
        )

        action_row.addWidget(btn_confirm)
        action_row.addStretch()
        action_row.addWidget(lbl_status)
        lay.addLayout(action_row)

        # Lưu panel refs
        refs = {
            "scan": scan,
            "sheet_combo": sheet_combo,
            "header_entry": header_entry,
            "col_lay": col_lay,
            "col_checkboxes": col_checkboxes,
            "col_combos": col_combos,
            "build_col_rows": build_col_rows,
            "lbl_confirm_status": lbl_status,
            "lbl_multi": lbl_multi,
            "btn_rescan": btn_rescan,
        }
        self._struct_panels[path] = refs

        # Gán command Dò lại
        def do_rescan(show_warning: bool = True):
            selected_sheet = sheet_combo.currentText()
            if self._rescan_callback is None:
                return
            try:
                new_scan = self._rescan_callback(path, selected_sheet)
            except Exception as exc:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Lỗi Dò lại", f"Không thể đọc lại file:\n{exc}")
                return
            refs["scan"] = new_scan
            hs2 = int(new_scan.get("header_start_row", new_scan.get("suggested_header_row", 0)))
            he2 = int(new_scan.get("header_end_row", hs2))
            ds2 = int(new_scan.get("data_start_row", hs2 + 1))
            lbl_multi.setText(
                f"Header từ dòng {hs2+1} đến dòng {he2+1} · Dữ liệu bắt đầu từ dòng {ds2+1}"
            )
            header_entry.setText(str(hs2))
            build_col_rows(
                new_scan.get("detected_columns", []),
                new_scan.get("suggested_mapping", {}),
                _saved=None,
            )
            lbl_status.setText("⬜ Chưa xác nhận (đã dò lại)")
            lbl_status.setStyleSheet(f"color: {C_TEXT_MUTED};")
            if path in self._file_structures:
                del self._file_structures[path]
            self.btn_next.setEnabled(False)
            self.lbl_struct_status.setText("")

        btn_rescan.clicked.connect(do_rescan)
        sheet_combo.currentTextChanged.connect(lambda _: do_rescan(show_warning=False))

        # Gán command Xác nhận
        def do_confirm():
            from PyQt6.QtWidgets import QMessageBox
            try:
                hr = int(header_entry.text())
            except ValueError:
                QMessageBox.warning(self, "Lỗi", "Dòng header phải là số nguyên.")
                return
            selected_cols = [c for c, cb in col_checkboxes.items() if cb.isChecked()]
            if not selected_cols:
                QMessageBox.warning(self, "Chưa chọn cột", "Vui lòng chọn ít nhất 1 cột.")
                return
            mapping = {c: col_combos[c].currentText() for c in selected_cols}

            if self._merge_mode == 1:
                mapped_stds = set(mapping.values())
                missing_name = "Họ và Tên" not in mapped_stds
                id_cols = {"Ngày Sinh", "Số CCCD/ID", "Số Điện Thoại"}
                has_id = bool(mapped_stds & id_cols)
                if missing_name or not has_id:
                    parts = []
                    if missing_name:
                        parts.append("• Họ và Tên  (bắt buộc)")
                    if not has_id:
                        parts.append("• Ít nhất 1 trong: Ngày Sinh / Số CCCD/ID / Số Điện Thoại")
                    QMessageBox.warning(
                        self, "Thiếu cột bắt buộc",
                        "Chế độ 1 yêu cầu ánh xạ:\n" + "\n".join(parts),
                    )
                    return

            scan_ref = refs.get("scan", scan)
            h_start = hr
            h_end = int(scan_ref.get("header_end_row", h_start))
            if h_end < h_start:
                h_end = h_start
            d_start = int(scan_ref.get("data_start_row", h_end + 1))
            structure = {
                "file_path": path,
                "sheet_name": sheet_combo.currentText(),
                "header_row": h_start,
                "header_start_row": h_start,
                "header_end_row": h_end,
                "data_start_row": d_start,
                "selected_columns": selected_cols,
                "column_mapping": mapping,
            }
            self._file_structures[path] = structure
            lbl_status.setText("✅ Đã xác nhận")
            lbl_status.setStyleSheet("color: #2E7D32;")
            if self.is_all_confirmed():
                self.btn_next.setEnabled(True)
                self.lbl_struct_status.setText(
                    f"✅ Tất cả {len(self._file_paths)} file đã xác nhận"
                )
                self.lbl_struct_status.setStyleSheet("color: #2E7D32;")

        btn_confirm.clicked.connect(do_confirm)

        # Auto-load profile
        if saved_profile:
            sp_sel = saved_profile.get("selected_columns", [])
            sp_map = saved_profile.get("column_mapping", {})
            mapped_stds = set(sp_map.values())
            id_cols = {"Ngày Sinh", "Số CCCD/ID", "Số Điện Thoại"}
            auto_ok = bool(sp_sel) and (
                self._merge_mode == 2
                or ("Họ và Tên" in mapped_stds and bool(mapped_stds & id_cols))
            )
            if auto_ok:
                sp_header = saved_profile.get("header_row", 0)
                h_s = int(scan.get("header_start_row", sp_header))
                h_e = int(scan.get("header_end_row", h_s))
                if h_e < h_s:
                    h_e = h_s
                d_s = int(scan.get("data_start_row", h_e + 1))
                self._file_structures[path] = {
                    "file_path": path,
                    "sheet_name": saved_profile.get("sheet_name", ""),
                    "header_row": sp_header, "header_start_row": h_s,
                    "header_end_row": h_e, "data_start_row": d_s,
                    "selected_columns": sp_sel, "column_mapping": sp_map,
                }
                lbl_status.setText("✅ Đã tự nạp profile")
                lbl_status.setStyleSheet("color: #2E7D32;")

        return panel

    @staticmethod
    def _open_file(path: str) -> None:
        import platform, subprocess
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as exc:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Lỗi", f"Không mở được file:\n{exc}")

    # ── DTO Getters ──────────────────────────────────────────────────
    def get_file_structures(self) -> Dict[str, dict]:
        return dict(self._file_structures)

    def is_all_confirmed(self) -> bool:
        return all(p in self._file_structures for p in self._file_paths)

    def get_struct_panels(self) -> Dict[str, dict]:
        return self._struct_panels


# ══════════════════════════════════════════════════════════════════════
# BƯỚC 1: CHỌN KHÓA QUÉT TRÙNG
# ══════════════════════════════════════════════════════════════════════
class DedupConfigScreen(QWidget):
    """
    Màn hình Bước 1: Chọn khóa quét trùng.

    DTO Getters:
        get_dedup_keys()   → List[str]
        get_sort_config()  → dict

    Controller gán:
        screen.btn_scan.clicked.connect(ctrl.handle_start_scan)
        screen.btn_back.clicked.connect(ctrl.handle_back_structure)
        screen.btn_home.clicked.connect(ctrl.handle_home)
    """

    DEDUP_KEYS = ["Họ và Tên", "Số CCCD/ID", "Số Điện Thoại", "Ngày Sinh"]

    def __init__(self, window: MainWindow, file_structures: Dict[str, dict]) -> None:
        super().__init__()
        self._window = window
        self._file_structures = file_structures
        self._checkboxes: Dict[str, QCheckBox] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        root.addWidget(_section_label("BƯỚC 1 / 2  –  CHỌN KHÓA QUÉT TRÙNG"))
        root.addWidget(_sub_label(
            "Các file đã xác nhận cấu trúc. Chọn khóa kết hợp để phát hiện bản ghi trùng."
        ))

        # Danh sách file
        file_frame = QFrame()
        file_frame.setStyleSheet(f"background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 8px;")
        file_lay = QVBoxLayout(file_frame)
        file_lay.setContentsMargins(14, 10, 14, 10)
        lbl_files = QLabel("Danh sách file đã nạp:")
        lbl_files.setFont(_qfont("Segoe UI", 13, bold=True))
        lbl_files.setStyleSheet("background: transparent;")
        file_lay.addWidget(lbl_files)
        for path, struct in self._file_structures.items():
            fname = os.path.basename(path)
            n_kept = len(struct.get("selected_columns", []))
            n_mapped = sum(1 for v in struct.get("column_mapping", {}).values()
                           if v and v != "Bỏ qua (Ignore)")
            row_lbl = QLabel(f"📄 {fname}  —  {n_kept} cột giữ lại, {n_mapped} cột đã ánh xạ")
            row_lbl.setFont(_qfont("Segoe UI", 12))
            row_lbl.setStyleSheet("color: #1565C0; background: transparent;")
            file_lay.addWidget(row_lbl)
        root.addWidget(file_frame)

        # Cấu hình khóa
        cfg_frame = QFrame()
        cfg_frame.setStyleSheet(f"background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 8px;")
        cfg_lay = QVBoxLayout(cfg_frame)
        cfg_lay.setContentsMargins(14, 10, 14, 10)
        cfg_lay.addWidget(QLabel("Chọn tiêu chí kết hợp để quét trùng  (nên chọn ít nhất 2 khóa):"))
        keys_row = QHBoxLayout()
        defaults = {"Họ và Tên", "Ngày Sinh"}
        for col in self.DEDUP_KEYS:
            cb = QCheckBox(col)
            cb.setChecked(col in defaults)
            cb.setFont(_qfont("Segoe UI", 12))
            keys_row.addWidget(cb)
            self._checkboxes[col] = cb
        keys_row.addStretch()
        cfg_lay.addLayout(keys_row)
        root.addWidget(cfg_frame)

        # Cấu hình sắp xếp
        sort_frame = QFrame()
        sort_frame.setStyleSheet(f"background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 8px;")
        sort_lay = QHBoxLayout(sort_frame)
        sort_lay.setContentsMargins(14, 10, 14, 10)
        sort_lay.addWidget(QLabel("Sắp xếp kết quả:"))
        all_mapped = []
        for struct in self._file_structures.values():
            for std_col in struct.get("column_mapping", {}).values():
                if std_col and std_col != "Bỏ qua (Ignore)" and std_col not in all_mapped:
                    all_mapped.append(std_col)
        sort_options = ["(Không sắp xếp)"] + (all_mapped if all_mapped else STANDARD_COLUMNS)
        self._sort_col_combo = QComboBox()
        self._sort_col_combo.setFixedWidth(220)
        self._sort_col_combo.addItems(sort_options)
        sort_lay.addWidget(self._sort_col_combo)
        sort_lay.addWidget(QLabel("Thứ tự:"))
        self._sort_dir_combo = QComboBox()
        self._sort_dir_combo.setFixedWidth(180)
        self._sort_dir_combo.addItems(["Tăng dần (A→Z)", "Giảm dần (Z→A)"])
        sort_lay.addWidget(self._sort_dir_combo)
        sort_lay.addStretch()
        root.addWidget(sort_frame)

        # Progress
        self.lbl_progress = QLabel("")
        self.lbl_progress.setFont(_qfont("Segoe UI", 12))
        self.lbl_progress.setStyleSheet(f"color: {C_TEXT_MUTED};")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        root.addWidget(self.lbl_progress)
        root.addWidget(self.progress_bar)

        # Nút xử lý
        self.btn_scan = _styled_btn(
            "▶  Tiến hành Quét & Khử trùng  ➔",
            bg=C_ACCENT, hover_bg="#b33900",
            height=46, bold=True, font_size=14,
        )
        root.addWidget(self.btn_scan)

        nav = QHBoxLayout()
        self.btn_back = _styled_btn("◀  Quay lại xác nhận cấu trúc",
                                     bg="#546E7A", hover_bg="#37474F", width=240, height=36)
        self.btn_home = _styled_btn("🏠  Về trang chủ", bg="transparent", fg=C_PRIMARY,
                                     hover_bg=C_BORDER, border=C_BORDER, width=140, height=36)
        nav.addWidget(self.btn_back)
        nav.addWidget(self.btn_home)
        nav.addStretch()
        root.addLayout(nav)

    # ── Public update methods ──────────────────────────────────────
    def update_progress(self, text: str, pct: float) -> None:
        self.lbl_progress.setText(text)
        self.progress_bar.setValue(max(0, min(100, int(pct))))

    def set_scan_button_state(self, enabled: bool) -> None:
        self.btn_scan.setEnabled(enabled)

    # ── DTO Getters ──────────────────────────────────────────────
    def get_dedup_keys(self) -> List[str]:
        return [col for col, cb in self._checkboxes.items() if cb.isChecked()]

    def get_sort_config(self) -> dict:
        col = self._sort_col_combo.currentText()
        if col == "(Không sắp xếp)":
            return {"col": None, "ascending": True}
        ascending = "Tăng dần" in self._sort_dir_combo.currentText()
        return {"col": col, "ascending": ascending}


# ══════════════════════════════════════════════════════════════════════
# BƯỚC 2: DUYỆT CẶP TRÙNG
# ══════════════════════════════════════════════════════════════════════
class ReviewScreen(QWidget):
    """
    Màn hình Bước 2: Duyệt từng cặp trùng.

    Dùng QTableView + ExcelTableModel để hiển thị bảng so sánh.

    Controller gán:
        screen.btn_approve.clicked.connect(ctrl.handle_approve)
        screen.btn_reject.clicked.connect(ctrl.handle_reject)
        screen.btn_skip_all.clicked.connect(ctrl.handle_skip_all)
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        root.addWidget(_section_label("BƯỚC 2 / 2  –  PHÊ DUYỆT HỢP NHẤT DÒNG TRÙNG"))

        self.lbl_counter = QLabel("")
        self.lbl_counter.setFont(_qfont("Segoe UI", 13, bold=True))
        self.lbl_counter.setStyleSheet(f"color: {C_PRIMARY};")
        root.addWidget(self.lbl_counter)

        # Bảng so sánh – dùng QTableView + ExcelTableModel
        self._review_model = ExcelTableModel()
        self.review_view = _make_table_view()
        self.review_view.setModel(self._review_model)
        self.review_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        root.addWidget(self.review_view, stretch=1)

        # Hint
        hint = QLabel("🟧 Giá trị KHÁC nhau   🟩 Giá trị GIỐNG nhau")
        hint.setFont(_qfont("Segoe UI", 11))
        hint.setStyleSheet(f"color: {C_TEXT_MUTED};")
        root.addWidget(hint)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_approve = _styled_btn(
            "✔  ĐÚNG – HỢP NHẤT, XÓA BẢN GHI 2",
            bg="#2E7D32", hover_bg="#1B5E20",
            width=280, height=46, bold=True,
        )
        self.btn_reject = _styled_btn(
            "✖  SAI – ĐÂY LÀ 2 NGƯỜI KHÁC NHAU",
            bg="#D32F2F", hover_bg="#C62828",
            width=280, height=46, bold=True,
        )
        self.btn_skip_all = _styled_btn(
            "⏭  Bỏ qua tất cả còn lại",
            bg="#546E7A", hover_bg="#37474F",
            width=180, height=46,
        )
        btn_row.addWidget(self.btn_approve)
        btn_row.addWidget(self.btn_reject)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_skip_all)
        root.addLayout(btn_row)

    # ── Public update methods ──────────────────────────────────────
    def load_pair(
        self,
        row1_data: dict,
        row2_data: dict,
        pair_index: int,
        total_pairs: int,
        merged_count: int,
    ) -> None:
        """Hiển thị cặp mới. Controller gọi từ main thread."""
        remaining = total_pairs - pair_index
        self.lbl_counter.setText(
            f"Cặp {pair_index + 1} / {total_pairs}   •   "
            f"Còn lại: {remaining}   •   Đã hợp nhất: {merged_count}"
        )
        # Xây dựng dữ liệu so sánh: mỗi hàng là 1 trường
        rows = []
        for col in STANDARD_COLUMNS:
            v1 = str(row1_data.get(col, ""))
            v2 = str(row2_data.get(col, ""))
            rows.append({"Trường thông tin": col,
                         "Bản ghi 1 (GIỮ LẠI)": v1,
                         "Bản ghi 2 (nghi trùng)": v2})
        self._review_model.load_data(
            rows,
            columns=["Trường thông tin", "Bản ghi 1 (GIỮ LẠI)", "Bản ghi 2 (nghi trùng)"],
        )


# ══════════════════════════════════════════════════════════════════════
# MÀN HÌNH KẾT QUẢ
# ══════════════════════════════════════════════════════════════════════
class FinalScreen(QWidget):
    """
    Màn hình kết quả cuối: preview bảng + nút xuất.
    Dùng QTableView + ExcelTableModel để hiển thị hàng triệu dòng nhẹ.

    Controller gán:
        screen.btn_export.clicked.connect(ctrl.handle_export)
        screen.btn_reconfig.clicked.connect(ctrl.handle_back_dedup)
        screen.btn_home.clicked.connect(ctrl.handle_home)
    """

    def __init__(
        self,
        window: MainWindow,
        final_df,
        total_input: int,
        n_deleted: int,
        n_files: int,
    ) -> None:
        super().__init__()
        self._window = window
        self._build_ui(final_df, total_input, n_deleted, n_files)

    def _build_ui(self, df, total_input, n_deleted, n_files) -> None:
        import pandas as pd
        total_output = len(df) if df is not None else 0

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        # Summary cards
        summary_row = QHBoxLayout()
        for label, value, color in [
            ("📥 Dòng đầu vào",      str(total_input),  C_PRIMARY),
            ("🗑️ Đã hợp nhất & xóa", str(n_deleted),    C_DANGER),
            ("✅ Kết quả cuối",       str(total_output), C_SUCCESS),
            ("📁 File đã nạp",        str(n_files),      "#6A1B9A"),
        ]:
            card = QFrame()
            card.setFixedSize(180, 70)
            card.setStyleSheet(f"background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 10px;")
            cl = QVBoxLayout(card)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_l = QLabel(label)
            lbl_l.setFont(_qfont("Segoe UI", 12))
            lbl_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_l.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none;")
            lbl_v = QLabel(value)
            lbl_v.setFont(_qfont("Segoe UI", 22, bold=True))
            lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_v.setStyleSheet(f"color: {color}; border: none;")
            cl.addWidget(lbl_l)
            cl.addWidget(lbl_v)
            summary_row.addWidget(card)
        summary_row.addStretch()
        root.addLayout(summary_row)

        # Preview bảng dùng QTableView + ExcelTableModel
        self._model = ExcelTableModel()
        if df is not None and not df.empty:
            self._model.load_data(df)
        self._table = _make_table_view()
        self._table.setModel(self._model)
        root.addWidget(self._table, stretch=1)

        if total_output > 0:
            lbl_note = QLabel(
                f"(Hiển thị đầy đủ {total_output} dòng – file xuất chứa đầy đủ.)"
            )
            lbl_note.setFont(_qfont("Segoe UI", 11))
            lbl_note.setStyleSheet(f"color: {C_TEXT_MUTED};")
            root.addWidget(lbl_note)

        # Nav buttons
        btn_row = QHBoxLayout()
        self.btn_export = _styled_btn("📤  Xuất file Excel", bg=C_SUCCESS, hover_bg="#1B5E20",
                                       width=200, height=46, bold=True, font_size=14)
        self.btn_reconfig = _styled_btn("◀  Quay lại chọn khóa quét",
                                         bg="#546E7A", hover_bg="#37474F", width=220, height=46)
        self.btn_home = _styled_btn("🏠  Về trang chủ", bg="transparent", fg=C_PRIMARY,
                                     hover_bg=C_BORDER, border=C_BORDER, width=140, height=46)
        btn_row.addWidget(self.btn_export)
        btn_row.addWidget(self.btn_reconfig)
        btn_row.addWidget(self.btn_home)
        btn_row.addStretch()
        root.addLayout(btn_row)


# ══════════════════════════════════════════════════════════════════════
# CHẾ ĐỘ 2: LEFT JOIN KEY SELECTOR
# ══════════════════════════════════════════════════════════════════════
class LeftJoinKeyScreen(QWidget):
    """
    Màn hình Chế độ 2: Cấu hình cặp khóa đối chiếu (Sequential Left Join).

    DTO Getter:
        get_key_pair_config()  → List[Dict[str, str]]

    Controller gán:
        screen.btn_start.clicked.connect(ctrl.handle_start_join)
        screen.btn_back.clicked.connect(ctrl.handle_home)
    """

    def __init__(
        self, window: "MainWindow", master_cols: List[str], aux_cols: List[str], previous_config: List[Dict[str, str]] = None
    ) -> None:
        super().__init__()
        self._window = window
        self._master_cols = master_cols
        self._aux_cols = aux_cols
        self._previous_config = previous_config or []
        self._pair_widgets: List[Dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(8)

        # Step bar
        step_bar = QFrame()
        step_bar.setStyleSheet("background: #EEF2FF; border-radius: 8px;")
        step_lay = QHBoxLayout(step_bar)
        step_lay.setContentsMargins(16, 6, 16, 6)
        for label, active in [
            ("① Xác nhận cấu trúc file", False),
            ("② Cấu hình cặp khóa ghép", True),
            ("③ Chạy gộp & xuất kết quả", False),
        ]:
            lbl = QLabel(label)
            lbl.setFont(_qfont("Segoe UI", 12, bold=active))
            lbl.setStyleSheet(f"color: {'#E65100' if active else '#9E9E9E'}; background: transparent;")
            step_lay.addWidget(lbl)
            step_lay.addSpacing(16)
        step_lay.addStretch()
        root.addWidget(step_bar)

        root.addWidget(_section_label("BƯỚC 2 / 3  –  CẤU HÌNH CẶP KHÓA GHÉP"))
        root.addWidget(_info_box(
            "🔑  Khóa ghép là cột dùng để ĐỐI CHIẾU dữ liệu giữa File Gốc và File Bổ sung.\n"
            "     Ví dụ: nếu cả 2 file đều có cột 'Họ và Tên', hãy ghép cặp đó.\n"
            "     Có thể thêm nhiều cặp khóa để tăng độ chính xác.",
            bg="#FFF8E1", fg="#5D4037",
        ))

        # Card cặp khóa
        card = MainWindow.make_card()
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(12, 10, 12, 10)
        card_lay.setSpacing(6)

        # Header hàng
        hdr_row = QHBoxLayout()
        for text, w in [("Cột File Gốc", 220), ("→", 30), ("Cột File Bổ sung", 240)]:
            lbl = QLabel(text)
            lbl.setFont(_qfont("Segoe UI", 12, bold=True))
            lbl.setFixedWidth(w)
            lbl.setStyleSheet(f"color: {C_PRIMARY};")
            hdr_row.addWidget(lbl)
        hdr_row.addStretch()
        card_lay.addLayout(hdr_row)

        # Scroll area cho các cặp khóa
        self._pairs_scroll = QScrollArea()
        self._pairs_scroll.setWidgetResizable(True)
        self._pairs_scroll.setFixedHeight(260)
        self._pairs_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._pairs_container = QWidget()
        self._pairs_container.setStyleSheet("background: transparent;")
        self._pairs_layout = QVBoxLayout(self._pairs_container)
        self._pairs_layout.setSpacing(4)
        self._pairs_layout.setContentsMargins(0, 0, 0, 0)
        self._pairs_layout.addStretch()
        self._pairs_scroll.setWidget(self._pairs_container)
        card_lay.addWidget(self._pairs_scroll)

        btn_add = _styled_btn("＋  Thêm cặp khóa", bg="#E8F5E9", fg=C_SUCCESS,
                               hover_bg="#C8E6C9", border=C_SUCCESS, width=180, height=32)
        btn_add.clicked.connect(self._add_key_pair)
        card_lay.addWidget(btn_add, alignment=Qt.AlignmentFlag.AlignLeft)

        root.addWidget(card, stretch=1)

        # Nav buttons
        nav_row = QHBoxLayout()
        self.btn_back = MainWindow.make_ghost_btn("◀  Quay lại", width=160, height=40)
        self.btn_start = MainWindow.make_accent_btn("🚀  Bắt đầu Gộp Chọn Lọc  ➔", width=260, height=42)
        self.btn_start.setEnabled(False)
        self.lbl_pair_status = QLabel("⚠️  Chưa có cặp khóa hợp lệ")
        self.lbl_pair_status.setFont(_qfont("Segoe UI", 12))
        self.lbl_pair_status.setStyleSheet(f"color: {C_WARN};")
        nav_row.addWidget(self.btn_back)
        nav_row.addStretch()
        nav_row.addWidget(self.lbl_pair_status)
        nav_row.addWidget(self.btn_start)
        root.addLayout(nav_row)

        # Thêm cặp theo cấu hình cũ hoặc auto-select
        if self._previous_config:
            for pair in self._previous_config:
                self._add_key_pair(pair.get("master_col", ""), pair.get("aux_col", ""))
        else:
            default_master = "Họ và Tên" if "Họ và Tên" in self._master_cols else ""
            default_aux = "Họ và Tên" if "Họ và Tên" in self._aux_cols else ""
            self._add_key_pair(default_master, default_aux)

    def _add_key_pair(self, master_default: str = "", aux_default: str = "") -> None:
        """Thêm một hàng cặp khóa."""
        row_w = QWidget()
        row_w.setStyleSheet("background: transparent;")
        row_lay = QHBoxLayout(row_w)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.setSpacing(6)

        m_combo = QComboBox()
        m_combo.setFixedWidth(220)
        m_combo.addItems(self._master_cols)
        if master_default in self._master_cols:
            m_combo.setCurrentText(master_default)

        lbl_arrow = QLabel("→")
        lbl_arrow.setFont(_qfont("Segoe UI", 14))
        lbl_arrow.setFixedWidth(24)
        lbl_arrow.setStyleSheet(f"color: {C_TEXT_MUTED};")

        a_combo = QComboBox()
        a_combo.setFixedWidth(240)
        a_combo.addItems(self._aux_cols)
        if aux_default in self._aux_cols:
            a_combo.setCurrentText(aux_default)

        wdict = {"master_combo": m_combo, "aux_combo": a_combo, "widget": row_w}

        btn_del = _styled_btn("✕", bg="#FFEBEE", fg=C_DANGER, hover_bg="#FFCDD2",
                               border="#FFCDD2", width=28, height=28, font_size=12)
        btn_del.clicked.connect(lambda: self._remove_pair(row_w, wdict))

        row_lay.addWidget(m_combo)
        row_lay.addWidget(lbl_arrow)
        row_lay.addWidget(a_combo)
        row_lay.addWidget(btn_del)
        row_lay.addStretch()

        # Chèn vào trước stretch cuối
        idx = self._pairs_layout.count() - 1
        self._pairs_layout.insertWidget(idx, row_w)
        self._pair_widgets.append(wdict)
        self._refresh_status()

    def _remove_pair(self, widget: QWidget, wdict: dict) -> None:
        widget.deleteLater()
        if wdict in self._pair_widgets:
            self._pair_widgets.remove(wdict)
        self._refresh_status()

    def _refresh_status(self) -> None:
        valid = self.get_key_pair_config()
        n = len(valid)
        if n == 0:
            self.lbl_pair_status.setText("⚠️  Chưa có cặp khóa hợp lệ")
            self.lbl_pair_status.setStyleSheet(f"color: {C_WARN};")
            self.btn_start.setEnabled(False)
        else:
            self.lbl_pair_status.setText(f"✅  {n} cặp khóa hợp lệ")
            self.lbl_pair_status.setStyleSheet(f"color: {C_SUCCESS};")
            self.btn_start.setEnabled(True)

    # ── DTO Getter ────────────────────────────────────────────────
    def get_key_pair_config(self) -> List[Dict[str, str]]:
        return [
            {"master_col": w["master_combo"].currentText(),
             "aux_col": w["aux_combo"].currentText()}
            for w in self._pair_widgets
            if w["master_combo"].currentText() not in ("(Không dùng)", "")
            and w["aux_combo"].currentText() not in ("(Không dùng)", "")
        ]


# ══════════════════════════════════════════════════════════════════════
# CHẾ ĐỘ 2: KẾT QUẢ LEFT JOIN
# ══════════════════════════════════════════════════════════════════════
class LeftJoinResultScreen(QWidget):
    """
    Màn hình kết quả Chế độ 2.
    Dùng QTableView + ExcelTableModel – hiển thị toàn bộ dữ liệu không giới hạn.

    Controller gán:
        screen.btn_export.clicked.connect(ctrl.handle_export_join)
        screen.btn_rekey.clicked.connect(ctrl.handle_back_key_selector)
        screen.btn_home.clicked.connect(ctrl.handle_home)
    """

    def __init__(
        self,
        window: MainWindow,
        result_df,
        key_cols: List[str],
    ) -> None:
        super().__init__()
        self._window = window
        self._build_ui(result_df, key_cols)

    def _build_ui(self, df, key_cols: List[str]) -> None:
        n_rows = len(df) if df is not None else 0
        n_cols_count = len(df.columns) if df is not None else 0

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(8)

        root.addWidget(_section_label("✅  KẾT QUẢ GỘP CHỌN LỌC", color=C_SUCCESS))

        stats_row = QHBoxLayout()
        for text, color in [
            (f"📄  File Gốc giữ nguyên: {n_rows} dòng", C_PRIMARY),
            (f"📊  Tổng số cột: {n_cols_count}", C_SUCCESS),
            (f"🔑  Khóa chính: {', '.join(key_cols)}", C_ACCENT),
        ]:
            lbl = QLabel(text)
            lbl.setFont(_qfont("Segoe UI", 12, bold=True))
            lbl.setStyleSheet(f"color: {color};")
            stats_row.addWidget(lbl)
            stats_row.addSpacing(20)
        stats_row.addStretch()
        root.addLayout(stats_row)

        # Preview bảng – QTableView + ExcelTableModel (không giới hạn dòng)
        self._model = ExcelTableModel()
        if df is not None and not df.empty:
            self._model.load_data(df)
        self._table = _make_table_view()
        self._table.setModel(self._model)
        root.addWidget(self._table, stretch=1)

        lbl_note = QLabel(
            f"(Hiển thị đầy đủ {n_rows} dòng – file xuất chứa đầy đủ.)"
        )
        lbl_note.setFont(_qfont("Segoe UI", 11))
        lbl_note.setStyleSheet(f"color: {C_TEXT_MUTED};")
        root.addWidget(lbl_note)

        btn_row = QHBoxLayout()
        self.btn_export = MainWindow.make_success_btn("💾  XUẤT FILE EXCEL", width=220, height=46)
        self.btn_rekey  = MainWindow.make_ghost_btn("◀  Chọn lại Khóa", width=180, height=46)
        self.btn_home   = MainWindow.make_ghost_btn("🏠  Trang chủ", width=150, height=46)
        btn_row.addWidget(self.btn_export)
        btn_row.addWidget(self.btn_rekey)
        btn_row.addWidget(self.btn_home)
        btn_row.addStretch()
        root.addLayout(btn_row)