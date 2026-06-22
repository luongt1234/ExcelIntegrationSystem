import json
import os
import sys
import sqlite3
from typing import Optional, Dict, List, Tuple
from datetime import datetime


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
        return os.path.join(db_dir, "learning_memory.db")
    else:
        # Development environment
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "learning_memory.db")


class LocalLearningManager:
    """
    Quản lý bộ nhớ lưu trữ cục bộ, phục vụ tính năng tự học hoàn toàn offline.
    Nâng cấp v3: thêm bảng app_config (cấu hình ứng dụng) và row_snapshots (snapshot dòng dữ liệu).
    """

    # ------------------------------------------------------------------
    # Giá trị cấu hình mặc định
    # ------------------------------------------------------------------
    _DEFAULT_CONFIG: Dict[str, str] = {
        "operation_mode":              "PROFILE_MATCHING",
        "catalog_similarity_threshold": "0.60",
        "conflict_separator":          " | ",
    }

    def __init__(self, db_path: str = None):
        self.db_path = db_path if db_path is not None else _get_db_path()
        self._init_db()

    def _init_db(self):
        """Khởi tạo toàn bộ schema SQLite cần thiết nếu chưa tồn tại."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            # Bảng ánh xạ cột đã học
            c.execute("""
                CREATE TABLE IF NOT EXISTS column_mappings (
                    user_header     TEXT NOT NULL,
                    standard_header TEXT NOT NULL,
                    frequency       INTEGER DEFAULT 1,
                    last_used       TEXT,
                    PRIMARY KEY (user_header, standard_header)
                )
            """)

            # Bảng lịch sử phiên xử lý
            c.execute("""
                CREATE TABLE IF NOT EXISTS session_log (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_time    TEXT NOT NULL,
                    files_processed INTEGER DEFAULT 0,
                    rows_input      INTEGER DEFAULT 0,
                    rows_output     INTEGER DEFAULT 0,
                    pairs_found     INTEGER DEFAULT 0,
                    pairs_merged    INTEGER DEFAULT 0
                )
            """)

            # Bảng cấu hình ứng dụng (mới v3)
            c.execute("""
                CREATE TABLE IF NOT EXISTS app_config (
                    key        TEXT PRIMARY KEY,
                    value      TEXT,
                    updated_at TEXT
                )
            """)

            # Bảng snapshot dòng dữ liệu (mới v3)
            c.execute("""
                CREATE TABLE IF NOT EXISTS row_snapshots (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT,
                    row_id      INTEGER,
                    source_file TEXT,
                    row_json    TEXT,
                    created_at  TEXT
                )
            """)

            # Bảng hồ sơ cấu trúc file đã xác nhận (mới v4)
            c.execute("""
                CREATE TABLE IF NOT EXISTS file_structure_profiles (
                    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_key           TEXT UNIQUE NOT NULL,
                    file_name_hint        TEXT,
                    sheet_name            TEXT,
                    header_row            INTEGER,
                    selected_columns_json TEXT,
                    column_mapping_json   TEXT,
                    last_used             TEXT,
                    header_end_row        INTEGER,
                    data_start_row        INTEGER
                )
            """)

            # Migration an toàn: thêm cột mới nếu DB cũ chưa có
            existing_columns = {
                row[1]
                for row in c.execute("PRAGMA table_info(file_structure_profiles)")
            }
            if "header_end_row" not in existing_columns:
                c.execute(
                    "ALTER TABLE file_structure_profiles ADD COLUMN header_end_row INTEGER"
                )
            if "data_start_row" not in existing_columns:
                c.execute(
                    "ALTER TABLE file_structure_profiles ADD COLUMN data_start_row INTEGER"
                )

            conn.commit()

        # Điền các giá trị mặc định nếu key chưa tồn tại
        self._seed_default_config()

    def _seed_default_config(self):
        """Chèn giá trị mặc định vào app_config nếu key chưa có — không ghi đè giá trị hiện tại."""
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            for key, value in self._DEFAULT_CONFIG.items():
                conn.execute("""
                    INSERT OR IGNORE INTO app_config (key, value, updated_at)
                    VALUES (?, ?, ?)
                """, (key, value, now))
            conn.commit()

    # ------------------------------------------------------------------
    # API: Ánh xạ cột  (giữ nguyên từ v2)
    # ------------------------------------------------------------------

    def remember_mapping(self, user_header: str, standard_header: str):
        """Ghi nhớ hoặc tăng tần suất ánh xạ cột do người dùng xác nhận."""
        if not user_header or not standard_header:
            return
        uh = str(user_header).strip().lower()
        sh = str(standard_header).strip()
        now = datetime.now().isoformat(timespec="seconds")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO column_mappings (user_header, standard_header, frequency, last_used)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(user_header, standard_header)
                DO UPDATE SET frequency = frequency + 1, last_used = excluded.last_used
            """, (uh, sh, now))
            conn.commit()

    def get_learned_mapping(self, user_header: str) -> Optional[str]:
        """Lấy tiêu đề chuẩn hóa đã học dựa trên tần suất cao nhất."""
        uh = str(user_header).strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT standard_header FROM column_mappings
                WHERE user_header = ?
                ORDER BY frequency DESC LIMIT 1
            """, (uh,)).fetchone()
        return row[0] if row else None

    def get_all_mappings(self) -> List[Tuple[str, str, int]]:
        """Trả về toàn bộ ánh xạ đã học: (user_header, standard_header, frequency)."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT user_header, standard_header, frequency
                FROM column_mappings
                ORDER BY frequency DESC
            """).fetchall()
        return rows

    def forget_mapping(self, user_header: str):
        """Xóa toàn bộ ánh xạ của một tiêu đề gốc (dùng khi người dùng muốn reset)."""
        uh = str(user_header).strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM column_mappings WHERE user_header = ?", (uh,))
            conn.commit()

    # ------------------------------------------------------------------
    # API: Lịch sử phiên  (giữ nguyên từ v2)
    # ------------------------------------------------------------------

    def log_session(self, files_processed: int, rows_input: int,
                    rows_output: int, pairs_found: int, pairs_merged: int):
        """Ghi nhật ký một phiên xử lý vào cơ sở dữ liệu."""
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO session_log
                    (session_time, files_processed, rows_input, rows_output, pairs_found, pairs_merged)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (now, files_processed, rows_input, rows_output, pairs_found, pairs_merged))
            conn.commit()

    def get_session_history(self, limit: int = 20) -> List[dict]:
        """Lấy lịch sử các phiên xử lý gần nhất."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM session_log
                ORDER BY id DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # API: Cấu hình ứng dụng  (mới v3)
    # ------------------------------------------------------------------

    def set_config(self, key: str, value) -> None:
        """
        Lưu hoặc cập nhật một giá trị cấu hình.
        value được ép sang str trước khi lưu; None lưu thành chuỗi rỗng.
        """
        str_value = "" if value is None else str(value)
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO app_config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key)
                DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """, (key, str_value, now))
            conn.commit()

    def get_config(self, key: str, default=None) -> Optional[str]:
        """
        Lấy giá trị cấu hình dạng str.
        Trả về default nếu key không tồn tại.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM app_config WHERE key = ?", (key,)
            ).fetchone()
        return row[0] if row is not None else default

    def get_float_config(self, key: str, default: float = 0.0) -> float:
        """
        Lấy giá trị cấu hình dưới dạng float.
        Trả về default nếu key không tồn tại hoặc không parse được.
        """
        raw = self.get_config(key)
        if raw is None:
            return default
        try:
            return float(raw)
        except (ValueError, TypeError):
            return default

    def get_int_config(self, key: str, default: int = 0) -> int:
        """
        Lấy giá trị cấu hình dưới dạng int.
        Trả về default nếu key không tồn tại hoặc không parse được.
        """
        raw = self.get_config(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except (ValueError, TypeError):
            return default

    # ------------------------------------------------------------------
    # API: Snapshot dòng dữ liệu  (mới v3)
    # ------------------------------------------------------------------

    def save_row_snapshot(self, session_id: str, row_id: int,
                          source_file: str, row_dict: dict) -> None:
        """
        Lưu snapshot một dòng dữ liệu (dạng dict) vào bảng row_snapshots.
        JSON được encode với ensure_ascii=False và default=str để an toàn với mọi kiểu dữ liệu.
        """
        row_json = json.dumps(row_dict, ensure_ascii=False, default=str)
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO row_snapshots (session_id, row_id, source_file, row_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, row_id, source_file, row_json, now))
            conn.commit()

    def load_row_snapshots(self, session_id: str) -> List[dict]:
        """
        Tải toàn bộ snapshot của một phiên theo session_id.
        Mỗi phần tử trả về là dict gốc đã parse từ JSON, kèm thêm các trường meta:
          _snapshot_id, _row_id, _source_file, _created_at.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT id, row_id, source_file, row_json, created_at
                FROM row_snapshots
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,)).fetchall()

        result = []
        for r in rows:
            try:
                data = json.loads(r["row_json"])
            except (json.JSONDecodeError, TypeError):
                data = {}
            data["_snapshot_id"]  = r["id"]
            data["_row_id"]       = r["row_id"]
            data["_source_file"]  = r["source_file"]
            data["_created_at"]   = r["created_at"]
            result.append(data)
        return result

    # ------------------------------------------------------------------
    # API: Hồ sơ cấu trúc file đã xác nhận  (mới v4)
    # ------------------------------------------------------------------

    def save_structure_profile(self, profile_key: str, file_name_hint: str,
                               structure_dict: dict) -> None:
        """
        Lưu hoặc cập nhật hồ sơ cấu trúc file đã xác nhận.
        structure_dict cần có: sheet_name, header_row, selected_columns, column_mapping.
        Tùy chọn thêm: header_end_row, data_start_row.
        """
        now = datetime.now().isoformat(timespec="seconds")
        selected_json = json.dumps(
            structure_dict.get("selected_columns", []), ensure_ascii=False
        )
        mapping_json = json.dumps(
            structure_dict.get("column_mapping", {}), ensure_ascii=False
        )
        header_end_row = structure_dict.get("header_end_row", None)
        data_start_row = structure_dict.get("data_start_row", None)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO file_structure_profiles
                    (profile_key, file_name_hint, sheet_name, header_row,
                     selected_columns_json, column_mapping_json, last_used,
                     header_end_row, data_start_row)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_key)
                DO UPDATE SET
                    file_name_hint        = excluded.file_name_hint,
                    sheet_name            = excluded.sheet_name,
                    header_row            = excluded.header_row,
                    selected_columns_json = excluded.selected_columns_json,
                    column_mapping_json   = excluded.column_mapping_json,
                    last_used             = excluded.last_used,
                    header_end_row        = excluded.header_end_row,
                    data_start_row        = excluded.data_start_row
            """, (
                profile_key,
                file_name_hint,
                structure_dict.get("sheet_name", ""),
                int(structure_dict.get("header_row", 0)),
                selected_json,
                mapping_json,
                now,
                int(header_end_row) if header_end_row is not None else None,
                int(data_start_row) if data_start_row is not None else None,
            ))
            conn.commit()

    def load_structure_profile(self, profile_key: str) -> Optional[dict]:
        """
        Tải hồ sơ cấu trúc theo profile_key.
        Trả về dict có đủ các key: sheet_name, header_row, selected_columns,
        column_mapping, file_name_hint, last_used, header_end_row, data_start_row
        — hoặc None nếu không tìm thấy.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM file_structure_profiles WHERE profile_key = ?",
                (profile_key,)
            ).fetchone()
        if row is None:
            return None
        try:
            selected_columns = json.loads(row["selected_columns_json"] or "[]")
        except (json.JSONDecodeError, TypeError):
            selected_columns = []
        try:
            column_mapping = json.loads(row["column_mapping_json"] or "{}")
        except (json.JSONDecodeError, TypeError):
            column_mapping = {}
        return {
            "profile_key":      row["profile_key"],
            "file_name_hint":   row["file_name_hint"],
            "sheet_name":       row["sheet_name"],
            "header_row":       row["header_row"],
            "selected_columns": selected_columns,
            "column_mapping":   column_mapping,
            "last_used":        row["last_used"],
            "header_end_row":   row["header_end_row"],   # None nếu record cũ chưa có
            "data_start_row":   row["data_start_row"],   # None nếu record cũ chưa có
        }

    def find_similar_structure_profile(self, file_name_hint: str) -> Optional[dict]:
        """
        Tìm hồ sơ gần đúng theo tên file (không phân biệt hoa thường, bỏ qua phần đường dẫn).
        Ưu tiên trả về hồ sơ được dùng gần nhất.
        """
        hint_lower = os.path.basename(file_name_hint).lower()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM file_structure_profiles ORDER BY last_used DESC"
            ).fetchall()
        for row in rows:
            stored_hint = os.path.basename(row["file_name_hint"] or "").lower()
            if stored_hint and stored_hint == hint_lower:
                return self.load_structure_profile(row["profile_key"])
        return None