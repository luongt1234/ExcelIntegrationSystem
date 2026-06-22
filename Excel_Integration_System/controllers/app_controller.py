"""
controllers/app_controller.py
===============================
AppController – Điều phối điều hướng toàn cục và Toolbar (PyQt6).

Trách nhiệm:
    • Quản lý việc chuyển đổi giữa các Màn hình (Screen) trong QStackedWidget.
    • Cung cấp hàm show_* để các Controller khác gọi khi cần chuyển bước.
    • Lắng nghe sự kiện từ Toolbar (Export, Help, Theme) và Hotkeys.
"""

from __future__ import annotations

import os
import webbrowser
from typing import TYPE_CHECKING, Optional

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QMessageBox, QWidget

if TYPE_CHECKING:
    from views.main_window import MainWindow
    from controllers.people_controller import PeopleController
    from controllers.goods_controller import GoodsController


class AppController:
    """
    AppController quản lý View gốc (MainWindow) và điều hướng.
    """

    def __init__(
        self,
        window: "MainWindow",
        people_ctrl: "PeopleController",
        goods_ctrl: "GoodsController",
    ) -> None:
        self.window = window
        self.people_ctrl = people_ctrl
        self.goods_ctrl = goods_ctrl

        self._current_mode: str = "home"  # 'home', 'people', 'goods'
        self._current_screen: Optional[QWidget] = None

        self._bind_toolbar()
        self._bind_hotkeys()

    def _bind_toolbar(self) -> None:
        """Gán command cho các nút trên Toolbar."""
        self.window.btn_export.clicked.connect(self.handle_export)
        self.window.btn_help.clicked.connect(self.show_help)
        self.window.btn_theme.clicked.connect(self.toggle_theme)

    def _bind_hotkeys(self) -> None:
        """Gán phím tắt toàn cục."""
        # Export (Ctrl+E)
        sc_export = QShortcut(QKeySequence("Ctrl+E"), self.window)
        sc_export.activated.connect(self.handle_export)

        # Help (F1)
        sc_help = QShortcut(QKeySequence("F1"), self.window)
        sc_help.activated.connect(self.show_help)

        # Home (Escape)
        sc_home = QShortcut(QKeySequence("Esc"), self.window)
        sc_home.activated.connect(self.show_home)

    def _switch_screen(self, screen_widget: QWidget) -> None:
        """Đổi màn hình trong QStackedWidget một cách an toàn."""
        # Nếu đã có màn hình hiện tại, xóa nó đi để giải phóng bộ nhớ
        if self._current_screen is not None:
            self.window.stack.removeWidget(self._current_screen)
            self._current_screen.deleteLater()

        # Thêm màn hình mới và hiển thị
        self.window.stack.addWidget(screen_widget)
        self.window.stack.setCurrentWidget(screen_widget)
        self._current_screen = screen_widget

    # ==================================================================
    # ĐIỀU HƯỚNG TỔNG QUÁT
    # ==================================================================
    def handle_export(self) -> None:
        """Phân luồng nút Export trên Toolbar tùy theo mode hiện tại."""
        if not self.window.btn_export.isEnabled():
            return
            
        if self._current_mode == "people":
            if hasattr(self.people_ctrl, "handle_export"):
                self.people_ctrl.handle_export()
            elif hasattr(self.people_ctrl, "handle_export_join"):
                self.people_ctrl.handle_export_join()
        elif self._current_mode == "goods":
            if hasattr(self.goods_ctrl, "handle_export_goods"):
                self.goods_ctrl.handle_export_goods()
        else:
            QMessageBox.information(self.window, "Export", "Không có dữ liệu để xuất ở trang chủ.")

    def show_help(self) -> None:
        """Mở file hướng dẫn hoặc link."""
        try:
            help_path = os.path.abspath("Huong_dan_su_dung.pdf")
            if os.path.exists(help_path):
                import platform
                import subprocess
                if platform.system() == 'Darwin':
                    subprocess.call(('open', help_path))
                elif platform.system() == 'Windows':
                    os.startfile(help_path)
                else:
                    subprocess.call(('xdg-open', help_path))
            else:
                webbrowser.open("https://github.com/vinhnguyen2409/DataMergePro")
        except Exception as e:
            QMessageBox.critical(self.window, "Lỗi", f"Không mở được hướng dẫn:\n{e}")

    def toggle_theme(self) -> None:
        """Chuyển đổi giao diện Sáng / Tối."""
        current = self.window.get_current_theme()
        new_theme = "Dark" if current == "Light" else "Light"
        self.window.apply_theme(new_theme)

    # ==================================================================
    # CÁC HÀM SHOW SCREEN
    # ==================================================================
    def show_home(self) -> None:
        """Hiển thị HomeScreen."""
        from views.screens.home_screen import HomeScreen

        self._current_mode = "home"
        self.window.set_header_mode("Trang chủ")
        self.window.set_export_enabled(False)
        self.window.update_status("Sẵn sàng")

        screen = HomeScreen(self.window)
        self._switch_screen(screen)

        # Gán lệnh: click Bắt đầu → chuyển sang màn hình chọn chế độ
        screen.btn_person.clicked.connect(self.show_mode_selection)
        screen.btn_goods.clicked.connect(self.show_goods_start)

        # Lưu screen reference (cho UI Editor reload)
        self.people_ctrl._home_screen = None  # Không còn dùng home_screen để browse
        self._home_screen = screen


    # ── Màn hình chọn file ───────────────────────────────────────────────
    def show_file_select_screen(self) -> None:
        """Hiển thị FileSelectScreen – màn hình chọn file (không phân biệt gốc/phụ)."""
        from views.screens.file_select_screen import FileSelectScreen

        self._current_mode = "people"
        self.window.set_header_mode("Gộp Hồ Sơ: Chọn file")
        self.window.set_export_enabled(False)

        screen = FileSelectScreen(self.window)
        self._switch_screen(screen)

        # Nếu đã có file từ lần trước, hiển thị lại
        if self.people_ctrl._selected_files:
            screen.set_selected_files(self.people_ctrl._selected_files)

        self.people_ctrl._file_select_screen = screen
        screen.btn_back.clicked.connect(self.show_mode_selection)
        screen.btn_browse.clicked.connect(
            lambda: self._handle_browse_for_file_select(screen)
        )
        screen.btn_proceed.clicked.connect(
            lambda: self.people_ctrl.handle_proceed_to_structure(screen)
        )

    def _handle_browse_for_file_select(self, screen) -> None:
        """Mở dialog chọn file và cập nhật FileSelectScreen."""
        from PyQt6.QtWidgets import QFileDialog
        
        mode = self.people_ctrl._merge_mode
        if mode == 3:
            file, _ = QFileDialog.getOpenFileName(
                self.window,
                "Chọn 1 file Excel cần chuẩn hóa",
                "",
                "Excel Files (*.xlsx *.xls)",
            )
            files = [file] if file else []
        else:
            files, _ = QFileDialog.getOpenFileNames(
                self.window,
                "Chọn file Excel cần gộp",
                "",
                "Excel Files (*.xlsx *.xls)",
            )
            
        if not files:
            return
        self.people_ctrl._selected_files = list(files)
        screen.set_selected_files(files)

    def show_source_file_select(self) -> None:
        """
        Hiển thị SourceFileSelectScreen – chỉ định file gốc / file phụ.
        Chỉ gọi khi chọn chế độ "Bổ sung Thông Tin" (mode 2).
        """
        from views.screens.source_file_select_screen import SourceFileSelectScreen

        self._current_mode = "people"
        self.window.set_header_mode("Bổ Sung Thông Tin: Chỉ định file gốc & phụ")
        self.window.set_export_enabled(False)

        files = self.people_ctrl._selected_files
        screen = SourceFileSelectScreen(self.window, files)
        self._switch_screen(screen)

        screen.btn_back.clicked.connect(self.show_mode_selection)
        screen.btn_confirm.clicked.connect(
            lambda: self._handle_source_files_confirmed(screen)
        )

    def _handle_source_files_confirmed(self, screen) -> None:
        """
        Sau khi xác nhận file gốc/phụ → sắp xếp lại danh sách file
        (file gốc ở đầu) và tiếp tục vào UnifiedKeyConfigScreen.
        """
        from PyQt6.QtWidgets import QMessageBox
        ordered = screen.get_ordered_files()
        if len(ordered) < 2:
            QMessageBox.warning(
                self.window,
                "Chưa đủ file",
                "Cần ít nhất 1 File Gốc và 1 File Phụ để thực hiện Bổ sung Thông Tin.",
            )
            return
        # Cập nhật thứ tự file vào controller (file gốc đầu)
        self.people_ctrl._selected_files = ordered
        # Đã chọn xong gốc/phụ -> Tiến hành quét cấu trúc
        self.people_ctrl._scan_all_files()

    # ── Flow People ──────────────────────────────────────────────────
    def show_structure_confirm(self, file_paths, scan_results, saved_profiles,
                               rescan_callback=None, **kwargs) -> None:
        """Hiển thị StructureConfirmScreen (Bước 0)."""
        from views.screens.merge_people_screen import StructureConfirmScreen

        self._current_mode = "people"
        self.window.set_header_mode("Gộp Hồ Sơ: Xác nhận cấu trúc")
        self.window.set_export_enabled(False)

        screen = StructureConfirmScreen(
            self.window,
            file_paths, scan_results, saved_profiles,
            rescan_callback=rescan_callback,
            **kwargs
        )
        self._switch_screen(screen)

        # Nút Tiếp theo → chuyển qua màn hình cấu hình chuyên sâu
        screen.btn_back.clicked.connect(self.show_file_select_screen)
        screen.btn_home.clicked.connect(self.show_home)
        screen.btn_next.clicked.connect(lambda: self.people_ctrl.handle_structure_confirmed(screen))

    def show_mode_selection(self) -> None:
        """Hiển thị ModeSelectionScreen (Chọn 1 trong 3 chế độ)."""
        from views.screens.mode_selection_screen import ModeSelectionScreen

        self.window.set_header_mode("Gộp Hồ Sơ: Chọn phương án")
        self.window.set_export_enabled(False)

        screen = ModeSelectionScreen(self.window)
        self._switch_screen(screen)

        def _on_mode_selected(mode: int) -> None:
            self.people_ctrl._merge_mode = mode
            self.show_file_select_screen()

        screen.on_mode_selected = _on_mode_selected
        screen.on_back = self.show_home

    def show_unified_key_config(self, file_structures, merge_mode: int, auto_keys=None) -> None:
        """Hiển thị UnifiedKeyConfigScreen (Cấu hình khóa chung)."""
        from views.screens.unified_key_config_screen import UnifiedKeyConfigScreen

        self._current_mode = "people"
        self.window.set_header_mode("Gộp Hồ Sơ: Cấu hình khóa")

        screen = UnifiedKeyConfigScreen(self.window, file_structures, merge_mode, auto_keys)
        self._switch_screen(screen)

        screen.btn_back.clicked.connect(self.show_mode_selection)
        screen.btn_home.clicked.connect(self.show_home)
        screen.btn_scan.clicked.connect(lambda: self.people_ctrl.handle_start_processing(screen))

    def show_drag_drop_mapping(self, file_paths, aux_cols_by_file, pre_confirmed_structures=None) -> None:
        """Hiển thị DragDropMappingScreen (Click-to-Pair ghép cột cho Bổ sung thông tin)."""
        from views.screens.drag_drop_mapping_screen import DragDropMappingScreen

        self._current_mode = "people"
        self.window.set_header_mode("Bổ Sung Thông Tin: Ghép cột")

        master_fp = file_paths[0]
        master_cols = aux_cols_by_file.get(master_fp, [])

        aux_cols_by_file_only = {}
        for fp in file_paths[1:]:
            aux_cols_by_file_only[fp] = aux_cols_by_file.get(fp, [])

        screen = DragDropMappingScreen(
            self.window,
            master_cols,
            aux_cols_by_file_only,
            pre_confirmed_structures=pre_confirmed_structures,
        )
        self._switch_screen(screen)

        # Quay lại Xác nhận cấu trúc
        screen.btn_back.clicked.connect(
            lambda: self.show_structure_confirm(
                self.people_ctrl._selected_files,
                self.people_ctrl._scan_results,
                self.people_ctrl._saved_profiles,
                pre_confirmed_structures=dict(self.people_ctrl._file_structures),
                rescan_callback=self.people_ctrl._make_rescan_callback(),
            )
        )
        screen.btn_next.clicked.connect(lambda: self.people_ctrl.handle_drag_drop_confirmed(screen))

    def show_data_cleaner_screen(self, file_structures) -> None:
        """Hiển thị DataCleanerScreen (Dọn dẹp 1 file)."""
        from views.screens.data_cleaner_screen import DataCleanerScreen

        self._current_mode = "people"
        self.window.set_header_mode("Dọn Dẹp & Chuẩn Hóa: Sắp xếp cột phân loại")

        screen = DataCleanerScreen(self.window, file_structures)
        self._switch_screen(screen)

        # Nút Quay lại
        screen.btn_back.clicked.connect(lambda: self.show_structure_confirm(
            self.people_ctrl._selected_files,
            self.people_ctrl._scan_results,
            self.people_ctrl._saved_profiles,
            pre_confirmed_structures=dict(self.people_ctrl._file_structures),
            rescan_callback=self.people_ctrl._make_rescan_callback(),
        ))
        # Nút Thực hiện → chạy dọn dẹp rồi chuyển sang màn hình xem trước kết quả
        screen.btn_clean.clicked.connect(lambda: self.people_ctrl.handle_start_cleaning(screen))

    def show_data_cleaner_result(self, result_df) -> None:
        """Hiển thị DataCleanerResultScreen (Xem trước kết quả Dọn dẹp & Chuẩn hóa)."""
        from views.screens.data_cleaner_screen import DataCleanerResultScreen

        self._current_mode = "people"
        self.window.set_header_mode("Dọn Dẹp & Chuẩn Hóa: Xem trước kết quả")
        self.window.set_export_enabled(True)

        screen = DataCleanerResultScreen(self.window, result_df)
        self._switch_screen(screen)

        # Nút Quay lại → về màn hình cấu hình dọn dẹp trước đó
        screen.btn_back.clicked.connect(
            lambda: self.show_data_cleaner_screen(self.people_ctrl._file_structures)
        )
        # Nút Xuất Excel → mở dialog lưu file, xuất toàn bộ dữ liệu (không bị cắt)
        screen.btn_export.clicked.connect(self.people_ctrl.handle_export_clean)

    def show_people_review(self) -> None:
        """Hiển thị ReviewScreen (Bước 2) - Dùng nếu auto-merge tắt."""
        from views.screens.merge_people_screen import ReviewScreen

        self._current_mode = "people"
        self.window.set_header_mode("Gộp Hồ Sơ: Duyệt thủ công")

        screen = ReviewScreen(self.window)
        self._switch_screen(screen)

        screen.btn_approve.clicked.connect(lambda: self.people_ctrl.handle_approve(screen))
        screen.btn_reject.clicked.connect(lambda: self.people_ctrl.handle_reject(screen))
        screen.btn_skip_all.clicked.connect(lambda: self.people_ctrl.handle_skip_all(screen))

        self.people_ctrl._load_pair_to_review(screen)

    def show_people_final(self, final_df, total_input, n_deleted, n_files) -> None:
        """Hiển thị FinalScreen (Kết quả)."""
        from views.screens.merge_people_screen import FinalScreen

        self._current_mode = "people"
        self.window.set_header_mode("Gộp Hồ Sơ: Kết quả")
        self.window.set_export_enabled(True)

        screen = FinalScreen(
            self.window,
            final_df, total_input, n_deleted, n_files
        )
        self._switch_screen(screen)

        screen.btn_export.clicked.connect(self.people_ctrl.handle_export)
        screen.btn_home.clicked.connect(self.show_home)
        screen.btn_reconfig.clicked.connect(
            lambda: self.show_unified_key_config(
                self.people_ctrl._file_structures,
                merge_mode=self.people_ctrl._merge_mode,
            )
        )

    # ── Flow Chế độ 2 (Left Join) ────────────────────────────────────
    def show_left_join_result(self, result_df, key_cols) -> None:
        from views.screens.merge_people_screen import LeftJoinResultScreen

        self._current_mode = "people"
        self.window.set_header_mode("Gộp Chọn Lọc: Kết quả")
        self.window.set_export_enabled(True)

        screen = LeftJoinResultScreen(self.window, result_df, key_cols)
        self._switch_screen(screen)

        screen.btn_export.clicked.connect(self.people_ctrl.handle_export_join)
        screen.btn_home.clicked.connect(self.show_home)
        screen.btn_rekey.clicked.connect(self.people_ctrl.handle_back_drag_drop_mapping)

    # ── Flow Goods ───────────────────────────────────────────────────
    def show_goods_start(self) -> None:
        """Hiển thị GoodsStartScreen."""
        from views.screens.merge_goods_screen import GoodsStartScreen

        self._current_mode = "goods"
        self.window.set_header_mode("Gộp Hàng Hóa: Chọn file")
        self.window.set_export_enabled(False)

        screen = GoodsStartScreen(self.window)
        self._switch_screen(screen)

        screen.btn_back.clicked.connect(self.show_home)
        screen.btn_select_input.clicked.connect(lambda: self.goods_ctrl.handle_select_input(screen))
        screen.btn_select_catalog.clicked.connect(lambda: self.goods_ctrl.handle_select_catalog(screen))
        screen.btn_proceed.clicked.connect(lambda: self.goods_ctrl.handle_run_matcher(screen))

    def show_goods_tabs(self) -> None:
        """Hiển thị GoodsTabScreen."""
        from views.screens.merge_goods_screen import GoodsTabScreen

        self._current_mode = "goods"
        self.window.set_header_mode("Gộp Hàng Hóa: Xét duyệt")
        self.window.set_export_enabled(False)

        approved = self.goods_ctrl.get_approved_items()
        pending  = self.goods_ctrl.get_pending_items()
        rejected = self.goods_ctrl.get_rejected_items()

        screen = GoodsTabScreen(
            self.window,
            approved, pending, rejected,
            on_approve_fn=self.goods_ctrl.handle_approve_item,
            on_reject_fn=self.goods_ctrl.handle_reject_item,
            on_restore_fn=self.goods_ctrl.handle_restore_item,
        )
        self._switch_screen(screen)

        screen.btn_back.clicked.connect(self.show_goods_start)
        screen.btn_refresh.clicked.connect(self.show_goods_tabs)
        screen.btn_export.clicked.connect(self.show_goods_final)

    def show_goods_final(self) -> None:
        """Hiển thị GoodsFinalScreen."""
        from views.screens.merge_goods_screen import GoodsFinalScreen

        self._current_mode = "goods"
        self.window.set_header_mode("Gộp Hàng Hóa: Kết quả")
        self.window.set_export_enabled(True)

        df = self.goods_ctrl.get_result_df()
        stats = self.goods_ctrl.get_stats()

        screen = GoodsFinalScreen(
            self.window,
            df, stats["n_approved"], stats["n_pending"], stats["n_rejected"]
        )
        self._switch_screen(screen)

        screen.btn_review.clicked.connect(self.show_goods_tabs)
        screen.btn_home.clicked.connect(self.show_home)
        screen.btn_export.clicked.connect(self.goods_ctrl.handle_export_goods)