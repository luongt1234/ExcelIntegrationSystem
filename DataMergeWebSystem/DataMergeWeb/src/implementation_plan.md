# Dynamic Multi-Level Header Naming

## Vấn đề hiện tại
Hiện tại, khi ứng dụng đọc một bảng có tiêu đề gộp (Multi-level header) như:
- Cấp 1: "Ngày nộp hồ sơ ứng tuyển"
- Cấp 2: "Trực tiếp", "Bưu điện"

Ứng dụng đang tự động nối chuỗi lại thành tên cột gốc là: **"Ngày nộp hồ sơ ứng tuyển - Trực tiếp"**.
Tuy nhiên, người dùng muốn có khả năng **nhấn vào các ô trên bảng hiển thị (Grid) để quyết định phần text nào sẽ được đưa vào tên cột cuối cùng**. 
- Nếu chọn cả cấp 1 và cấp 2: Tên cột là "Ngày nộp hồ sơ ứng tuyển - Trực tiếp".
- Nếu bỏ chọn cấp 1, chỉ chọn cấp 2: Tên cột sẽ chỉ lấy "Trực tiếp" và bỏ chữ "Ngày nộp hồ sơ ứng tuyển".

## Giải pháp đề xuất

Thay vì click vào ô Header trên Grid để tick/bỏ tick ô checkbox của cột (như hiện tại), ta sẽ đổi hành vi click này thành: **Bật/tắt việc sử dụng chữ của ô đó trong việc tạo tên cột mới (Tên sẽ được map sang)**.

### Chi tiết thay đổi (FileStructurePreview.jsx)

1. **Thêm state quản lý các ô Header bị loại bỏ (Ignored)**
   - `const [ignoredHeaderCells, setIgnoredHeaderCells] = useState(new Set());`
   - Mỗi ô trong `headerGrid` sẽ được định danh bằng tọa độ `rIdx-cIdx`.

2. **Cập nhật hàm click vào ô Header Grid**
   - Khi click vào một ô `(rIdx, cIdx)`, ta sẽ toggle tọa độ đó trong `ignoredHeaderCells`.
   - Ngay sau đó, quét lại toàn bộ các cột bị ảnh hưởng bởi ô này (thông qua `cell.coveredColumns`).
   - Với mỗi cột, xây dựng lại tên mới (`newName`) bằng cách:
     - Đi từ trên xuống dưới qua các hàng của `headerGrid` tại cột đó.
     - Thu thập text của các ô **không bị ignore**.
     - Nối lại bằng dấu ` - `.
   - Cập nhật state `mappings` với `newName` vừa tạo.

3. **Giao diện phản hồi**
   - Các ô trên Grid nếu bị ignore sẽ hiển thị mờ đi (ví dụ: nền xám nhạt, chữ gạch ngang hoặc mờ bớt) để người dùng biết là chữ đó không được lấy.
   - Các ô đang active sẽ sáng rõ.

## Open Questions
- Tính năng này sẽ ghi đè lên Tên Cột Mới (New Name) nếu người dùng đã tự gõ tay trước đó. Điều này có ổn không? (Thường là ổn vì đây là hành động chủ động của người dùng).

## User Review Required
Bạn vui lòng xác nhận xem cách này (bấm vào ô tiêu đề để loại bỏ/thêm chữ của ô đó vào tên cột cuối cùng) đã đúng với ý bạn chưa nhé!