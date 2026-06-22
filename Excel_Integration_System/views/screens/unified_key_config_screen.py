import os
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QProgressBar, QVBoxLayout, QWidget, QRadioButton, QButtonGroup
)

from views.main_window import (
    MainWindow,
    C_PRIMARY, C_ACCENT, C_BORDER, C_TEXT_MUTED, C_CARD,
    _qfont, _styled_btn, _section_label, _sub_label
)


class UnifiedKeyConfigScreen(QWidget):
    """
    Màn hình cấu hình khóa hợp nhất cho cả 2 chế độ: Nối dài và Bổ sung.
    """
    DEDUP_KEYS = ["Họ và Tên", "Số CCCD/ID", "Số Điện Thoại", "Ngày Sinh"]

    def __init__(self, window: MainWindow, file_structures: Dict[str, dict], merge_mode: int, auto_keys: Optional[List[str]] = None) -> None:
        super().__init__()
        self._window = window
        self._file_structures = file_structures
        self._merge_mode = merge_mode
        self._auto_keys = auto_keys or []
        
        self._checkboxes: Dict[str, QCheckBox] = {}
        self._radio_group = QButtonGroup(self)
        self._radios: Dict[str, QRadioButton] = {}
        
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        if self._merge_mode == 1:
            root.addWidget(_section_label("CẤU HÌNH KHÓA  –  LOẠI BỎ TRÙNG LẶP (TÙY CHỌN)"))
            root.addWidget(_sub_label("Bạn có muốn loại bỏ các dòng lặp lại sau khi nối không? Nếu có, hãy chọn các khóa đối chiếu."))
        else:
            root.addWidget(_section_label("CẤU HÌNH KHÓA  –  BỔ SUNG THÔNG TIN"))
            root.addWidget(_sub_label("Hãy chọn khóa đối chiếu duy nhất để kết nối dữ liệu giữa các file."))

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
        
        keys_row = QHBoxLayout()
        
        if self._merge_mode == 1:
            cfg_lay.addWidget(QLabel("Chọn tiêu chí để quét trùng (Có thể để trống nếu chỉ muốn nối thuần túy):"))
        else:
            cfg_lay.addWidget(QLabel("Chọn các khóa làm điểm tựa (chìa khóa) để ghép nối dữ liệu (Có thể chọn nhiều):"))
            
        all_mapped = []
        for struct in self._file_structures.values():
            for std_col in struct.get("column_mapping", {}).values():
                if std_col and std_col != "Bỏ qua (Ignore)" and std_col not in all_mapped:
                    all_mapped.append(std_col)
        
        options = self.DEDUP_KEYS if not all_mapped else all_mapped
        
        if self._merge_mode == 1:
            defaults = {"Họ và Tên", "Ngày Sinh"}
        else:
            if self._auto_keys:
                defaults = set(self._auto_keys)
            elif options:
                defaults = {options[0]}
            else:
                defaults = set()

        for col in options:
            cb = QCheckBox(col)
            cb.setChecked(col in defaults)
            cb.setFont(_qfont("Segoe UI", 12))
            keys_row.addWidget(cb)
            self._checkboxes[col] = cb

        keys_row.addStretch()
        cfg_lay.addLayout(keys_row)
        root.addWidget(cfg_frame)

        # Cấu hình sắp xếp (chỉ áp dụng cho Nối dài)
        if self._merge_mode == 1:
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
            # Dùng hardcode fallback tạm
            fallback_cols = ["Họ và Tên", "Số CCCD/ID", "Số Điện Thoại", "Ngày Sinh", "Mã Nhân Viên", "Giới Tính", "Địa Chỉ", "Email"]
            sort_options = ["(Không sắp xếp)"] + (all_mapped if all_mapped else fallback_cols)
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
        btn_text = "▶  Tiến hành Quét & Khử trùng  ➔" if self._merge_mode == 1 else "▶  Bắt đầu Bổ sung thông tin  ➔"
        self.btn_scan = _styled_btn(
            btn_text,
            bg=C_ACCENT, hover_bg="#b33900",
            height=46, bold=True, font_size=14,
        )
        root.addWidget(self.btn_scan)

        nav = QHBoxLayout()
        self.btn_back = _styled_btn("◀  Quay lại",
                                     bg="#546E7A", hover_bg="#37474F", width=160, height=36)
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
    def get_selected_keys(self) -> List[str]:
        return [col for col, cb in self._checkboxes.items() if cb.isChecked()]

    def get_sort_config(self) -> dict:
        if self._merge_mode != 1:
            return {"col": None, "ascending": True}
            
        col = self._sort_col_combo.currentText()
        if col == "(Không sắp xếp)":
            return {"col": None, "ascending": True}
        ascending = "Tăng dần" in self._sort_dir_combo.currentText()
        return {"col": col, "ascending": ascending}
