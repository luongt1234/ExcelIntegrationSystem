# DataMerge Web System

Hệ thống Tích hợp & Chuẩn hóa Dữ liệu (Excel) đa năng, được thiết kế theo kiến trúc Monolith (Clean Architecture) với Backend **.NET 8** và Frontend **ReactJS (Vite + TailwindCSS)**.

## 🌟 Chức Năng Cốt Lõi

1. **Dọn dẹp & Gộp Hồ Sơ (Dedup & Union)**
   - Gộp nhiều file Excel vào một bảng duy nhất.
   - Chọn các cột làm "Khóa chung".
   - Tự động nhận diện trùng lặp và loại bỏ (giữ lại dòng đầu tiên).
   - *Mode 2:* Dọn dẹp/Chuẩn hóa 1 file đơn lẻ.

2. **Bổ sung thông tin (Left Join)**
   - Giao diện kéo-thả (Drag & Drop) siêu trực quan để ghép cột từ file phụ sang file gốc.
   - Xử lý mượt mà dữ liệu lớn, tự động điền các thông tin khớp với "Khóa chung".

3. **Gộp Hàng Hóa (Catalog Matcher)**
   - So khớp thông minh chuỗi tên hàng hóa trong Input với danh mục chuẩn (Catalog) bằng thuật toán *Jaccard Similarity*.
   - Phân loại tự động ra 3 nhóm: **Đã duyệt** (trùng khớp cao), **Chờ duyệt** (khớp một phần), **Từ chối** (không khớp).

---

## 🏗 Kiến Trúc Hệ Thống

Hệ thống được chia làm 2 phần chính:

### 1. Frontend: `DataMergeWeb`
- **Công nghệ:** ReactJS, Vite, TailwindCSS.
- **Thư viện chính:**
  - `react-router-dom`: Quản lý định tuyến (Routing & Protected Routes).
  - `axios`: Giao tiếp API.
  - `lucide-react`: Hệ thống icon SVG nhẹ và đẹp.
  - `xlsx` (SheetJS): Đọc/xuất file Excel trực tiếp tại client.
- **Đặc điểm:** Giao diện Split-Screen hiện đại, hỗ trợ kéo thả file, Data Table tích hợp Pagination, Search, Sort.

### 2. Backend: `DataMergeServices`
- **Công nghệ:** .NET 8 (Web API).
- **Kiến trúc:** Clean Architecture (4 Layers: `Domain`, `Application`, `Infrastructure`, `API`).
- **Thành phần chính:**
  - `Entity Framework Core`: ORM quản lý database MySQL.
  - `EPPlus`: Đọc/Ghi file Excel tốc độ cao.
  - `JWT Bearer`: Xác thực và phân quyền người dùng.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### Yêu Cầu Hệ Thống
- [Node.js](https://nodejs.org/) (phiên bản v18 trở lên).
- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0).
- [MySQL](https://www.mysql.com/) Server (port 3306).

### Cài Đặt Cơ Sở Dữ Liệu
1. Mở file `DataMergeWebSystem/DataMergeServices/DataMerge.API/appsettings.json`.
2. Sửa thông tin kết nối `DefaultConnection` phù hợp với máy của bạn (user, password).
3. Mở Terminal/PowerShell tại thư mục `DataMergeWebSystem/DataMergeServices`.
4. Chạy lệnh tạo database và cập nhật Migration (đã cấu hình tự động Seed tài khoản `admin`/`admin`):
   ```bash
   dotnet ef database update --project DataMerge.Infrastructure --startup-project DataMerge.API
   ```

### Khởi Chạy Backend
Mở Terminal/PowerShell tại thư mục `DataMergeWebSystem/DataMergeServices`:
```bash
dotnet run --project DataMerge.API
```
*API sẽ chạy tại: `https://localhost:7198` hoặc theo cấu hình Kestrel của bạn.*

### Khởi Chạy Frontend
Mở một Terminal/PowerShell khác tại thư mục `DataMergeWebSystem/DataMergeWeb`:
```bash
npm install
npm run dev
```
*Frontend sẽ chạy tại: `http://localhost:5173` (hoặc cổng tương tự).*

---

## 🔑 Tài Khoản Đăng Nhập
Sau khi cài đặt DB, bạn có thể đăng nhập bằng tài khoản mặc định:
- **Tên đăng nhập:** `admin`
- **Mật khẩu:** `admin`

---

## 📂 Cấu Trúc Thư Mục
```text
ExcelIntegrationSystem/
│
├── DataMergeWebSystem/
│   ├── DataMergeServices/       # .NET 8 Backend
│   │   ├── DataMerge.Domain/      # Entity, Models, Interfaces cốt lõi
│   │   ├── DataMerge.Application/ # Các Interface dịch vụ (Business logic abstractions)
│   │   ├── DataMerge.Infrastructure/ # Xử lý Excel, Database context, EF Migrations
│   │   └── DataMerge.API/         # Controllers, Middleware, JWT, DI Setup
│   │
│   └── DataMergeWeb/            # ReactJS Vite Frontend
│       ├── src/
│       │   ├── components/        # BaseTable, Layout, FileUploader
│       │   ├── pages/             # Login, Home, PeopleMerge, InfoAppend, GoodsMerge
│       │   ├── services/          # Axios instance, excelService.js
│       │   └── App.jsx            # Router config
│       ├── tailwind.config.js
│       └── package.json
│
├── .gitignore
└── README.md
```
