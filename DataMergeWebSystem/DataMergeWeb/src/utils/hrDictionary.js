export const hrDictionaries = {
  "Họ và tên": ["họ và tên", "họ tên", "tên ứng viên", "tên nhân viên", "name", "full name", "fullname"],
  "Ngày sinh": ["ngày sinh", "sinh ngày", "dob", "date of birth", "năm sinh", "tháng sinh"],
  "Giới tính": ["giới tính", "phái", "nam/nữ", "gender", "sex"],
  "Số điện thoại": ["sđt", "số điện thoại", "điện thoại", "phone", "mobile", "tel", "đt"],
  "CCCD": ["cccd", "cmnd", "căn cước", "căn cước công dân", "chứng minh", "chứng minh thư", "số cccd", "số cmnd"],
  "Email": ["email", "thư điện tử", "e-mail", "mail"],
  "Địa chỉ": ["địa chỉ", "nơi ở", "thường trú", "tạm trú", "chỗ ở", "address"],
  "Quê quán": ["quê quán", "nơi sinh", "nguyên quán"],
  "Phòng ban": ["phòng ban", "bộ phận", "department", "đơn vị"],
  "Chức vụ": ["chức vụ", "chức danh", "vị trí", "position", "chuyên môn"],
  "Mã nhân viên": ["mã nhân viên", "mnv", "mã nv", "employee id", "mã ứng viên", "mã"],
  "Số báo danh": ["số báo danh", "sbd"],
  "Trạng thái": ["trạng thái", "tình trạng", "status"],
  "Ghi chú": ["ghi chú", "note", "nhận xét", "đánh giá"]
};

export const getStandardizedColumnName = (rawName) => {
  if (!rawName) return '';
  const normalizedRaw = rawName.toString().normalize('NFC').toLowerCase().trim();
  
  // 1. Exact match checking
  for (const [standard, variants] of Object.entries(hrDictionaries)) {
    if (variants.includes(normalizedRaw)) {
      return standard;
    }
  }

  // 2. Substring match checking (from longest to shortest variants to avoid premature matching)
  for (const [standard, variants] of Object.entries(hrDictionaries)) {
    const sortedVariants = [...variants].sort((a, b) => b.length - a.length);
    for (const v of sortedVariants) {
      if (normalizedRaw.includes(v)) {
        return standard;
      }
    }
  }

  return rawName.trim();
};
