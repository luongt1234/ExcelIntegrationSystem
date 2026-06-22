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

  // Xử lý Search
  const filteredData = useMemo(() => {
    if (!searchTerm) return data;
    return data.filter(row => 
      Object.values(row).some(val => 
        String(val).toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [data, searchTerm]);

  // Xử lý Sort
  const sortedData = useMemo(() => {
    let sortableItems = [...filteredData];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [filteredData, sortConfig]);

  // Xử lý Pagination
  const totalPages = Math.ceil(sortedData.length / rowsPerPage);
  const currentData = useMemo(() => {
    const start = (currentPage - 1) * rowsPerPage;
    return sortedData.slice(start, start + rowsPerPage);
  }, [sortedData, currentPage]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const handleExport = () => {
    const worksheet = XLSX.utils.json_to_sheet(sortedData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");
    XLSX.writeFile(workbook, exportFileName);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-full max-h-[80vh]">
      {/* Table Header / Toolbar */}
      <div className="p-4 border-b border-gray-200 flex flex-wrap items-center justify-between gap-4 bg-gray-50/50">
        <h2 className="text-lg font-semibold text-gray-800">{title} <span className="text-sm font-normal text-gray-500 ml-2">({sortedData.length} dòng)</span></h2>
        
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
                <tr key={rowIndex} className="hover:bg-blue-50/50 transition-colors">
                  {columns.map((col, colIndex) => (
                    <td key={colIndex} className="px-6 py-3 whitespace-nowrap text-sm text-gray-700 border-r border-gray-100 last:border-r-0">
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
          Hiển thị từ <span className="font-semibold">{(currentPage - 1) * rowsPerPage + 1}</span> đến <span className="font-semibold">{Math.min(currentPage * rowsPerPage, sortedData.length)}</span> trong <span className="font-semibold">{sortedData.length}</span> kết quả
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
