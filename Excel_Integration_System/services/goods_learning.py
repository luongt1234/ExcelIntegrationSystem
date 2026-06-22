"""
goods_learning.py
=================
Quản lý trạng thái học cho chức năng Gộp Hàng Hóa Thông Minh.
Lưu trữ bằng SQLite, hỗ trợ 3 trạng thái: APPROVED, PENDING, REJECTED.
"""

import sqlite3
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def _get_db_path():
    """Xác định đường dẫn database phù hợp cho cả development và packaged environment."""
    if getattr(sys, 'frozen', False):
        # Đang chạy trong packaged environment (PyInstaller, etc.)
        # Sử dụng thư mục dữ liệu người dùng
        if sys.platform == 'win32':
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            db_dir = os.path.join(appdata, 'DataMergePro')
        else:
            db_dir = os.path.expanduser('~/.datamergepro')
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, "goods_learning.db")
    else:
        # Development environment
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "goods_learning.db")


DB_PATH = _get_db_path()

STATUS_APPROVED = "APPROVED"
STATUS_PENDING  = "PENDING"
STATUS_REJECTED = "REJECTED"


class GoodsLearningManager:
    """Quản lý bộ nhớ học ánh xạ hàng hóa."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # KHỞI TẠO DB
    # ------------------------------------------------------------------
    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goods_mapping (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_name        TEXT    NOT NULL,
                    standard_name   TEXT    NOT NULL DEFAULT '',
                    similarity      REAL    NOT NULL DEFAULT 0.0,
                    status          TEXT    NOT NULL DEFAULT 'PENDING',
                    updated_at      TEXT    NOT NULL,
                    catalog_source  TEXT    NOT NULL DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_name ON goods_mapping(raw_name)
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # ------------------------------------------------------------------
    # LOAD DANH MỤC CHUẨN (ghi nhớ catalog)
    # ------------------------------------------------------------------
    def load_catalog(self, catalog_names: List[str], source: str = "") -> None:
        """Ghi nhớ danh sách tên chuẩn từ file danh mục."""
        now = datetime.now().isoformat()
        with self._conn() as conn:
            for name in catalog_names:
                name = name.strip()
                if not name:
                    continue
                # Nếu tên chuẩn chính xác 100% → auto APPROVED
                conn.execute("""
                    INSERT INTO goods_mapping (raw_name, standard_name, similarity, status, updated_at, catalog_source)
                    VALUES (?, ?, 1.0, ?, ?, ?)
                    ON CONFLICT(raw_name) DO NOTHING
                """, (name, name, STATUS_APPROVED, now, source))

    # ------------------------------------------------------------------
    # TRUY VẤN TRẠNG THÁI
    # ------------------------------------------------------------------
    def get_status_for_item(self, raw_name: str) -> Optional[Dict]:
        """Lấy thông tin mapping cho 1 tên hàng hóa."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT raw_name, standard_name, similarity, status FROM goods_mapping WHERE raw_name = ?",
                (raw_name,)
            ).fetchone()
        if row:
            return {"raw_name": row[0], "standard_name": row[1], "similarity": row[2], "status": row[3]}
        return None

    def get_approved_items(self) -> List[Dict]:
        return self._get_items_by_status(STATUS_APPROVED)

    def get_pending_items(self) -> List[Dict]:
        return self._get_items_by_status(STATUS_PENDING)

    def get_rejected_items(self) -> List[Dict]:
        return self._get_items_by_status(STATUS_REJECTED)

    def _get_items_by_status(self, status: str) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT raw_name, standard_name, similarity, status, updated_at FROM goods_mapping WHERE status = ? ORDER BY updated_at DESC",
                (status,)
            ).fetchall()
        return [
            {"raw_name": r[0], "standard_name": r[1], "similarity": r[2], "status": r[3], "updated_at": r[4]}
            for r in rows
        ]

    # ------------------------------------------------------------------
    # GHI / CẬP NHẬT TRẠNG THÁI
    # ------------------------------------------------------------------
    def set_status(self, raw_name: str, standard_name: str, status: str, similarity: float = 0.0) -> None:
        """Tạo hoặc cập nhật một mục."""
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO goods_mapping (raw_name, standard_name, similarity, status, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(raw_name) DO UPDATE SET
                    standard_name = excluded.standard_name,
                    similarity    = excluded.similarity,
                    status        = excluded.status,
                    updated_at    = excluded.updated_at
            """, (raw_name, standard_name, similarity, status, now))

    def move_item_to_approved(self, raw_name: str, standard_name: str) -> None:
        self.set_status(raw_name, standard_name, STATUS_APPROVED)

    def move_item_to_rejected(self, raw_name: str) -> None:
        """Đưa vào blacklist, giữ lại standard_name cũ (hoặc để trống)."""
        existing = self.get_status_for_item(raw_name)
        std = existing["standard_name"] if existing else ""
        sim = existing["similarity"] if existing else 0.0
        self.set_status(raw_name, std, STATUS_REJECTED, sim)

    def restore_item(self, raw_name: str) -> None:
        """Phục hồi từ REJECTED về APPROVED (nếu có standard_name)."""
        existing = self.get_status_for_item(raw_name)
        if existing and existing["standard_name"]:
            self.set_status(raw_name, existing["standard_name"], STATUS_APPROVED, existing["similarity"])
        else:
            self.set_status(raw_name, "", STATUS_PENDING, 0.0)

    # ------------------------------------------------------------------
    # XÓA / RESET
    # ------------------------------------------------------------------
    def delete_item(self, raw_name: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM goods_mapping WHERE raw_name = ?", (raw_name,))

    def clear_all(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM goods_mapping")

    # ------------------------------------------------------------------
    # LẤY MAPPING ĐÃ DUYỆT (dùng khi xuất file)
    # ------------------------------------------------------------------
    def get_approved_mapping(self) -> Dict[str, str]:
        """Trả về dict {raw_name: standard_name} cho tất cả APPROVED."""
        items = self.get_approved_items()
        return {item["raw_name"]: item["standard_name"] for item in items if item["standard_name"]}