import { useState, useMemo } from 'react';
import { Search, Download, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';
import * as XLSX from 'xlsx';

export default function BaseTable({ 
  columns, 
  data, 
  title = "Dữ liệu", 
  enableExport = true,
  exportFileName = "data.xlsx"
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const rowsPerPage = 15;

  // Phân tích và gộp nhóm theo STT 3 Cấp: Cấp 1 (A, B, C), Cấp 2 (I, II, III), Cấp 3 (1, 2, 3...)
  const enrichedData = useMemo(() => {
    let currentL1Id = 0;
    let currentL2Id = 0;

    return data.map((row, index) => {
      const sttKey = Object.keys(row).find(k => k.trim().toUpperCase() === 'STT' || k.trim().toUpperCase() === 'SỐ THỨ TỰ');
      const sttVal = sttKey && row[sttKey] != null ? String(row[sttKey]).trim().toUpperCase() : '';
      
      const isRoman = /^(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}(I{1,3}|IV|V|VI{1,3}|IX)?)$/.test(sttVal);
      const isAlphabet = /^[A-Z]$/.test(sttVal) && !isRoman;
      
      if (isAlphabet) {
        currentL1Id = index + 1; // ID cấp 1
        currentL2Id = 0; // Reset L2
        return { ...row, __isL1Header: true, __isL2Header: false, __l1Id: currentL1Id, __l2Id: -1 };
      }
      
      if (isRoman) {
        currentL2Id = index + 1; // ID cấp 2
        return { ...row, __isL1Header: false, __isL2Header: true, __l1Id: currentL1Id, __l2Id: currentL2Id };
      }

      // Dữ liệu con bình thường (1, 2, 3...)
      return { ...row, __isL1Header: false, __isL2Header: false, __l1Id: currentL1Id, __l2Id: currentL2Id || -1 };
    });
  }, [data]);

  // Xử lý Search
  const filteredData = useMemo(() => {
    if (!searchTerm) return enrichedData;
    return enrichedData.filter(row => 
      Object.keys(row).some(key => 
        !key.startsWith('__') && String(row[key]).toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [enrichedData, searchTerm]);

  // Xử lý Sort
  const sortedData = useMemo(() => {
    let sortableItems = [...filteredData];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        // 1. Cấp 1 (A, B, C): Giữ nguyên thứ tự gốc
        if (a.__l1Id !== b.__l1Id) return a.__l1Id - b.__l1Id;
        
        // Cùng Cấp 1: Dòng Header Cấp 1 phải đứng đầu
        if (a.__isL1Header) return -1;
        if (b.__isL1Header) return 1;

        // 2. Cấp 2 (I, II, III): Giữ nguyên thứ tự gốc bên trong Cấp 1
        if (a.__l2Id !== b.__l2Id) return a.__l2Id - b.__l2Id;

        // Cùng Cấp 2: Dòng Header Cấp 2 phải đứng đầu
        if (a.__isL2Header) return -1;
        if (b.__isL2Header) return 1;

        // 3. Các tập con (1, 2, 3...) bên trong cùng 1 Cấp 2 sẽ bị Sort!
        let valA = a[sortConfig.key];
        let valB = b[sortConfig.key];
        
        if (valA === null || valA === undefined) return 1;
        if (valB === null || valB === undefined) return -1;

        const keyLower = String(sortConfig.key).toLowerCase();

        // Chuẩn hóa Tên: Đảo Tên lên trước Họ để Sort (VD: 'Lê Thị Mây' -> 'Mây Lê Thị Mây')
        if (keyLower.includes('tên') || keyLower.includes('họ') || keyLower.includes('name')) {
          const getSortName = (name) => {
            const str = String(name).trim();
            const parts = str.split(' ');
            return parts.length > 1 ? `${parts[parts.length - 1]} ${str}` : str;
          };
          valA = getSortName(valA);
          valB = getSortName(valB);
        }

        // Chuẩn hóa Ngày tháng: dd/MM/yyyy hoặc ISO Date -> yyyyMMdd để Sort đúng theo Thời gian
        if (keyLower.includes('ngày') || keyLower.includes('tháng') || keyLower.includes('năm') || keyLower.includes('date')) {
          const parseDate = (str) => {
            const s = String(str).trim();
            // Định dạng dd/MM/yyyy
            const parts = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
            if (parts) {
              const day = parts[1].padStart(2, '0');
              const month = parts[2].padStart(2, '0');
              const year = parts[3];
              return parseInt(`${year}${month}${day}`, 10);
            }
            // Định dạng ISO Date (từ Backend trả về chưa qua displayData)
            if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(s)) {
              const d = new Date(s);
              if (!isNaN(d.getTime())) {
                const day = String(d.getDate()).padStart(2, '0');
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const year = d.getFullYear();
                return parseInt(`${year}${month}${day}`, 10);
              }
            }
            return s; // Fallback
          };
          valA = parseDate(valA);
          valB = parseDate(valB);
        }

        // Sử dụng Tiếng Việt (vi) để sort đúng bảng chữ cái (A, Ă, Â, B, C, D, Đ...)
        if (typeof valA === 'string' && typeof valB === 'string') {
          const compareResult = valA.localeCompare(valB, 'vi', { sensitivity: 'base' });
          return sortConfig.direction === 'asc' ? compareResult : -compareResult;
        }

        if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
        if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return sortableItems;
  }, [filteredData, sortConfig]);

  // Đánh lại Số thứ tự (STT) sau khi đã Sắp xếp
  const displayData = useMemo(() => {
    if (sortedData.length === 0) return sortedData;

    const sttKey = Object.keys(sortedData[0]).find(k => k.trim().toUpperCase() === 'STT' || k.trim().toUpperCase() === 'SỐ THỨ TỰ');
    if (!sttKey) return sortedData;

    let currentChildIndex = 1;
    return sortedData.map(row => {
      const newRow = { ...row };
      
      if (row.__isL1Header || row.__isL2Header) {
        currentChildIndex = 1; // Reset bộ đếm khi gặp Header mới
      } else if (sttKey) {
        newRow[sttKey] = currentChildIndex++;
      }

      // Format ISO Dates
      Object.keys(newRow).forEach(key => {
        if (!key.startsWith('__')) {
          const val = newRow[key];
          if (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(val)) {
            const d = new Date(val);
            if (!isNaN(d.getTime())) {
              const day = String(d.getDate()).padStart(2, '0');
              const month = String(d.getMonth() + 1).padStart(2, '0');
              const year = d.getFullYear();
              newRow[key] = `${day}/${month}/${year}`;
            }
          }
        }
      });
      
      return newRow;
    });
  }, [sortedData]);

  // Xử lý Pagination
  const totalPages = Math.ceil(displayData.length / rowsPerPage);
  const currentData = useMemo(() => {
    const start = (currentPage - 1) * rowsPerPage;
    return displayData.slice(start, start + rowsPerPage);
  }, [displayData, currentPage]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const handleExport = () => {
    // Xóa các trường nội bộ (__) trước khi xuất Excel
    const exportData = displayData.map(row => {
      const cleanRow = { ...row };
      Object.keys(cleanRow).forEach(key => {
        if (key.startsWith('__')) {
          delete cleanRow[key];
        }
      });
      return cleanRow;
    });

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");
    XLSX.writeFile(workbook, exportFileName);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-full max-h-[80vh]">
      {/* Table Header / Toolbar */}
      <div className="p-4 border-b border-gray-200 flex flex-wrap items-center justify-between gap-4 bg-gray-50/50">
        <h2 className="text-lg font-semibold text-gray-800">{title} <span className="text-sm font-normal text-gray-500 ml-2">({displayData.length} dòng)</span></h2>
        
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={16} className="text-gray-400" />
            </div>
            <input
              type="text"
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-64 shadow-sm transition-shadow"
              placeholder="Tìm kiếm..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1); // Reset page on search
              }}
            />
          </div>
          
          {enableExport && (
            <button 
              onClick={handleExport}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
            >
              <Download size={16} />
              <span>Xuất Excel</span>
            </button>
          )}
        </div>
      </div>

      {/* Table Content */}
      <div className="flex-1 overflow-auto">
        <table className="min-w-full divide-y divide-gray-200 border-collapse">
          <thead className="bg-gray-50 sticky top-0 z-10 shadow-sm">
            <tr>
              {columns.map((col, idx) => (
                <th 
                  key={idx}
                  onClick={() => handleSort(col.accessor)}
                  className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap border-r border-gray-200 last:border-r-0"
                >
                  <div className="flex items-center space-x-1">
                    <span>{col.Header}</span>
                    <ArrowUpDown size={14} className={sortConfig.key === col.accessor ? 'text-blue-500' : 'text-gray-400'} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currentData.length > 0 ? (
              currentData.map((row, rowIndex) => (
                <tr key={rowIndex} className={`transition-colors ${row.__isL1Header ? 'bg-orange-100 font-bold text-orange-900 shadow-sm border-y border-orange-300' : row.__isL2Header ? 'bg-amber-50/60 font-semibold text-gray-900 shadow-sm border-y border-amber-200' : 'hover:bg-blue-50/50'}`}>
                  {columns.map((col, colIndex) => (
                    <td key={colIndex} className="px-6 py-3 text-sm border-r border-gray-100 last:border-r-0 min-w-[120px] max-w-[400px] whitespace-normal break-words align-top">
                      {row[col.accessor] !== null && row[col.accessor] !== undefined ? String(row[col.accessor]) : '-'}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12 text-center text-gray-500">
                  Không tìm thấy dữ liệu.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Hiển thị từ <span className="font-semibold">{(currentPage - 1) * rowsPerPage + 1}</span> đến <span className="font-semibold">{Math.min(currentPage * rowsPerPage, displayData.length)}</span> trong <span className="font-semibold">{displayData.length}</span> kết quả
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed bg-white text-gray-600 transition-colors"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-gray-700 font-medium px-4">
            Trang {currentPage} / {totalPages || 1}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages || totalPages === 0}
            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed bg-white text-gray-600 transition-colors"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
