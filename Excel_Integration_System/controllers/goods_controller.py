"""
controllers/goods_controller.py
================================
GoodsController – Điều phối flow Gộp Hàng Hóa (PyQt6).

Trách nhiệm:
    • Gán command cho nút GoodsStartScreen.
    • Gọi GoodsProcessor trong background thread.
    • Cập nhật View qua QTimer.singleShot().
    • DTO Getter từ GoodsStartScreen.get_goods_config().

Nguyên tắc:
    - KHÔNG import View.
    - Callback UI luôn qua QTimer.singleShot(0, lambda: ...).
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFileDialog, QMessageBox

if TYPE_CHECKING:
    from views.main_window import MainWindow
    from services.goods_processor import GoodsProcessor
    from services.goods_learning import GoodsLearningManager


class GoodsController:
    """
    Controller cho flow Gộp Hàng Hóa.
    Khởi tạo tại main.py với DI:
        ctrl = GoodsController(window, goods_processor, goods_lm)
    """

    def __init__(
        self,
        window: "MainWindow",
        goods_processor: "GoodsProcessor",
        goods_lm: "GoodsLearningManager",
        app_controller=None,
    ) -> None:
        self.window = window
        self.goods_processor = goods_processor
        self.goods_lm = goods_lm
        self.app_ctrl = app_controller

        # ── State nội bộ ──────────────────────────────────────────────
        self._input_df = None
        self._name_col: str = ""
        self._catalog_col: str = ""
        self._catalog_names = []

    # ==================================================================
    # 1. CHỌN FILE
    # ==================================================================
    def handle_select_input(self, goods_start_screen) -> None:
        """
        Mở dialog chọn file đầu vào.
        Sau đó cập nhật View qua hàm set_input_file() — KHÔNG truy cập widget.
        """
        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Chọn file Excel đầu vào",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if not path:
            return
        try:
            cols = self.goods_processor.get_column_names(path)
            # Gọi setter trên View — View sẽ tự cập nhật combo
            goods_start_screen.set_input_file(path, cols)
        except Exception as e:
            QMessageBox.critical(self.window, "Lỗi đọc file", str(e))

    def handle_select_catalog(self, goods_start_screen) -> None:
        """Mở dialog chọn file danh mục chuẩn."""
        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Chọn file danh mục chuẩn",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if not path:
            return
        try:
            cols = self.goods_processor.get_column_names(path)
            goods_start_screen.set_catalog_file(path, cols)
        except Exception as e:
            QMessageBox.critical(self.window, "Lỗi đọc file", str(e))

    def handle_run_matcher(self, goods_start_screen) -> None:
        """
        Lấy DTO từ GoodsStartScreen, validate, chạy matcher trong thread.
        NGUYÊN TẮC 3: Lấy dữ liệu qua Getter, không truy cập widget.
        """
        import os

        # ── Lấy DTO ──────────────────────────────────────────────────
        config = goods_start_screen.get_goods_config()
        input_file   = config["input_file"]
        name_col     = config["input_name_col"]
        catalog_file = config["catalog_file"]
        catalog_col  = config["catalog_col"]

        if not input_file:
            QMessageBox.warning(self.window, "Thiếu file", "Vui lòng chọn file Excel đầu vào.")
            return
        if not catalog_file:
            QMessageBox.warning(self.window, "Thiếu file", "Vui lòng chọn file danh mục chuẩn.")
            return

        try:
            self._input_df = self.goods_processor.read_input_file(input_file, name_col)
            self._catalog_names = self.goods_processor.read_catalog_file(catalog_file, catalog_col)
        except Exception as e:
            QMessageBox.critical(self.window, "Lỗi đọc file", str(e))
            return

        self._name_col = name_col
        self._catalog_col = catalog_col
        self.goods_lm.load_catalog(
            self._catalog_names,
            source=os.path.basename(catalog_file),
        )

        input_names = (
            self._input_df[name_col]
            .dropna().astype(str).str.strip().unique().tolist()
        )

        def worker() -> None:
            self.goods_processor.suggest_matches(input_names, self._catalog_names)
            # NGUYÊN TẮC 1: cập nhật UI qua QTimer.singleShot
            QTimer.singleShot(0, lambda: self._on_matcher_done())

        threading.Thread(target=worker, daemon=True).start()

    def _on_matcher_done(self) -> None:
        """Callback sau khi matcher hoàn tất (đã về main thread)."""
        if self.app_ctrl:
            self.app_ctrl.show_goods_tabs()

    # ==================================================================
    # 2. TAB DUYỆT
    # ==================================================================
    def handle_approve_item(self, raw_name: str, std_name: str) -> None:
        """Phê duyệt ánh xạ (gọi từ closure trong GoodsTabScreen)."""
        self.goods_lm.move_item_to_approved(raw_name, std_name)

    def handle_reject_item(self, raw_name: str) -> None:
        """Loại bỏ ánh xạ."""
        self.goods_lm.move_item_to_rejected(raw_name)

    def handle_restore_item(self, raw_name: str) -> None:
        """Khôi phục mục từ blacklist."""
        self.goods_lm.restore_item(raw_name)

    def handle_refresh_tabs(self) -> None:
        """Làm mới màn hình tab."""
        if self.app_ctrl:
            self.app_ctrl.show_goods_tabs()

    def handle_show_final(self) -> None:
        """Chuyển sang màn hình kết quả hàng hóa."""
        if self.app_ctrl:
            self.app_ctrl.show_goods_final()

    # ==================================================================
    # 3. KẾT QUẢ & XUẤT FILE
    # ==================================================================
    def handle_export_goods(self) -> None:
        """Xuất file kết quả hàng hóa."""
        if self._input_df is None:
            QMessageBox.warning(self.window, "Không có dữ liệu", "Chưa có dữ liệu để xuất.")
            return
        approved_map = self.goods_lm.get_approved_mapping()
        result_df = self.goods_processor.apply_approved_mappings(
            self._input_df, self._name_col,
            approved_map, output_column="Tên chuẩn",
        )
        save_path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Lưu kết quả hàng hóa",
            "",
            "Excel Files (*.xlsx)"
        )
        if not save_path:
            return
            
        if not save_path.lower().endswith('.xlsx'):
            save_path += '.xlsx'
            
        try:
            self.goods_processor.export_clean_excel(
                result_df, save_path,
                name_column=self._name_col, output_column="Tên chuẩn",
            )
            QMessageBox.information(
                self.window,
                "Xuất thành công",
                f"✅ Đã lưu {len(result_df)} dòng tại:\n{save_path}",
            )
        except Exception as e:
            QMessageBox.critical(self.window, "Lỗi xuất file", str(e))

    # ==================================================================
    # 4. DTO CHO AppController (lấy data để build màn hình)
    # ==================================================================
    def get_approved_items(self) -> list:
        return self.goods_lm.get_approved_items()

    def get_pending_items(self) -> list:
        return self.goods_lm.get_pending_items()

    def get_rejected_items(self) -> list:
        return self.goods_lm.get_rejected_items()

    def get_result_df(self):
        """Trả về DataFrame kết quả đã áp dụng approved mapping."""
        if self._input_df is None:
            return None
        approved_map = self.goods_lm.get_approved_mapping()
        return self.goods_processor.apply_approved_mappings(
            self._input_df, self._name_col,
            approved_map, output_column="Tên chuẩn",
        )

    def get_stats(self) -> dict:
        return {
            "n_approved": len(self.goods_lm.get_approved_items()),
            "n_pending":  len(self.goods_lm.get_pending_items()),
            "n_rejected": len(self.goods_lm.get_rejected_items()),
        }
