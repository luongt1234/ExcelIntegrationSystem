"""
main.py
=======
Bootstrap – Khởi chạy ứng dụng DataMerge Pro (Kiến trúc MVC v4.0 với PyQt6).

Nhiệm vụ duy nhất:
1. Khởi tạo QApplication.
2. Nạp các Service (DataProcessor, LocalLearningManager, ...).
3. Tạo View gốc (MainWindow).
4. Khởi tạo Controller và Bơm phụ thuộc (Dependency Injection).
5. Hiển thị màn hình Home và chạy app.exec().
"""

import sys
import ctypes
import logging
import traceback

# Bật DPI Awareness trên Windows để font chữ sắc nét
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        ctypes.windll.user32.SetProcessDPIAware()
    except AttributeError:
        pass

from PyQt6.QtWidgets import QApplication, QMessageBox

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AppBootstrap")

# Bắt lỗi không xác định (unhandled exceptions)
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Lỗi không xác định", exc_info=(exc_type, exc_value, exc_traceback))
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Hiển thị thông báo lỗi nếu QApplication đã tồn tại
    app = QApplication.instance()
    if app:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Lỗi hệ thống")
        msg_box.setText("Đã xảy ra lỗi nghiêm trọng. Xin vui lòng kiểm tra lại cấu hình hoặc dữ liệu.")
        msg_box.setDetailedText(msg)
        msg_box.exec()
    else:
        print(f"FATAL ERROR:\n{msg}", file=sys.stderr)

sys.excepthook = global_exception_handler


def main():
    logger.info("Đang khởi động DataMerge Pro MVC (PyQt6)...")
    
    # Khởi tạo QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Giao diện hiện đại đa nền tảng
    
    try:
        # Import components
        from views.main_window import MainWindow
        from services.learning_manager import LocalLearningManager
        from services.data_processor import DataProcessor
        from services.goods_learning import GoodsLearningManager
        from services.goods_processor import GoodsProcessor
        
        from controllers.people_controller import PeopleController
        from controllers.goods_controller import GoodsController
        from controllers.app_controller import AppController
        
        # 1. Khởi tạo Services (Layer 1)
        logger.info("Đang khởi tạo các Service...")
        lm = LocalLearningManager()
        processor = DataProcessor(lm)
        
        goods_lm = GoodsLearningManager()
        goods_processor = GoodsProcessor(goods_lm)
        
        # 2. Khởi tạo View gốc (Layer 2)
        logger.info("Đang khởi tạo View chính...")
        window = MainWindow()
        
        # 3. Khởi tạo Controllers (Layer 3) và Dependency Injection
        logger.info("Đang khởi tạo Controllers...")
        people_ctrl = PeopleController(window, processor, lm)
        goods_ctrl = GoodsController(window, goods_processor, goods_lm)
        
        app_ctrl = AppController(window, people_ctrl, goods_ctrl)
        
        # Link AppController lại vào các sub-controller (để chuyển đổi luồng)
        people_ctrl.app_ctrl = app_ctrl
        goods_ctrl.app_ctrl = app_ctrl
        
        # 4. Hiển thị màn hình Home và chạy loop
        logger.info("Hiển thị màn hình Home.")
        app_ctrl.show_home()
        window.show()
        
        # Chạy main event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Lỗi khởi tạo: {e}", exc_info=True)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Lỗi Khởi Động")
        msg_box.setText(f"Không thể khởi chạy ứng dụng:\n\n{e}")
        msg_box.exec()
        sys.exit(1)

if __name__ == "__main__":
    main()