import React, { useEffect, useState, useRef } from 'react';
import { FileText, Eye, CheckCircle, RefreshCcw, Maximize2, Minimize2 } from 'lucide-react';
import { getFileData } from '../services/excelService';

// Hàm helper để tạo tên cột Excel (A, B, C..., Z, AA, AB...)
const getColumnLetter = (colIndex) => {
  let letter = '';
  let temp = colIndex;
  while (temp >= 0) {
    letter = String.fromCharCode((temp % 26) + 65) + letter;
    temp = Math.floor(temp / 26) - 1;
  }
  return letter;
};

export default function FileStructurePreview({ file, isVerified, onVerify, onSheetChange, suggestedMappings = {} }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [mappings, setMappings] = useState(null);
  const [excludedGridCells, setExcludedGridCells] = useState({});
  const [editingCol, setEditingCol] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [viewMode, setViewMode] = useState('table');
  const [headerRowIndex, setHeaderRowIndex] = useState(0);
  const [previewColumn, setPreviewColumn] = useState(null);
  const [previewPosition, setPreviewPosition] = useState(null);
  const pressTimer = useRef(null);
  const isLongPress = useRef(false);

  const headers = file.headers?.length > 0 
    ? file.headers 
    : (data.length > 0 ? Object.keys(data[0]) : []);

  const buildColumnName = (colIdx, excludedMap = {}) => {
    if (!file.headerGrid || file.headerGrid.length === 0) {
      const orig = headers[colIdx] || '';
      return suggestedMappings[orig] || orig;
    }
    const parts = [];
    file.headerGrid.forEach((row, rIdx) => {
      row.forEach((cell, cIdx) => {
        if (cell.coveredColumns?.includes(colIdx)) {
          const cellKey = `${rIdx}_${cIdx}`;
          if (!excludedMap[cellKey] && cell.text && cell.text.trim() !== '') {
            const trimmed = cell.text.trim();
            if (parts.length === 0 || parts[parts.length - 1] !== trimmed) {
              parts.push(trimmed);
            }
          }
        }
      });
    });
    if (parts.length === 1) {
      const orig = parts[0];
      return suggestedMappings[orig] || suggestedMappings[headers[colIdx]] || orig;
    }
    return parts.length > 0 ? parts.join(' - ') : (headers[colIdx] || '');
  };

  useEffect(() => {
    if (!mappings || !file.headerGrid || file.headerGrid.length === 0) return;
    setMappings(prev => {
      const next = { ...prev };
      headers.forEach((h, idx) => {
        if (next[h]) {
          const autoName = buildColumnName(idx, excludedGridCells);
          next[h] = { ...next[h], newName: autoName };
        }
      });
      return next;
    });
  }, [excludedGridCells]);

  useEffect(() => {
    let mounted = true;
    const loadData = async () => {
      setLoading(true);
      try {
        const res = await getFileData(file.fileId, file.selectedSheet);
        if (mounted) {
          setData(res.data.slice(0, 15));
          
          // Initialize mappings
          const loadedHeaders = file.headers?.length > 0 ? file.headers : (res.data.length > 0 ? Object.keys(res.data[0]) : []);
          const initialMappings = {};
          loadedHeaders.forEach((h, idx) => {
            const defaultNewName = file.headerGrid?.length > 0 ? buildColumnName(idx, {}) : (suggestedMappings[h] || h);
            initialMappings[h] = { newName: defaultNewName, selected: true };
          });
          setMappings(initialMappings);
        }
      } catch (err) {
        if (mounted) setError('Không thể tải dữ liệu preview');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    loadData();
    return () => { mounted = false; };
  }, [file.fileId, file.selectedSheet, file.headers, suggestedMappings]);

  const toggleColumn = (colName) => {
    if (isLongPress.current) {
      isLongPress.current = false;
      return;
    }
    if (isVerified || editingCol === colName) return;
    setMappings(prev => ({
      ...prev,
      [colName]: { ...prev[colName], selected: !prev[colName].selected }
    }));
  };

  const startEdit = (e, colName) => {
    e.stopPropagation();
    if (isVerified) return;
    setEditingCol(colName);
    setEditValue(mappings[colName]?.newName || colName);
  };

  const handleEditKeyDown = (e, colName) => {
    if (e.key === 'Enter') {
      commitEdit(colName);
    } else if (e.key === 'Escape') {
      setEditingCol(null);
    }
  };

  const commitEdit = (colName) => {
    if (editValue.trim() !== '') {
      setMappings(prev => ({
        ...prev,
        [colName]: { ...prev[colName], newName: editValue.trim() }
      }));
    }
    setEditingCol(null);
  };

  const isColSelected = (colName) => mappings && mappings[colName] && mappings[colName].selected;

  const isGridHeaderSelected = (cellDto, cellKey) => {
    if (excludedGridCells[cellKey]) return false;
    if (!mappings || !cellDto.coveredColumns || cellDto.coveredColumns.length === 0) return false;
    return cellDto.coveredColumns.every(colIdx => mappings[headers[colIdx]]?.selected);
  };

  const handleGridHeaderClick = (cellDto, rIdx, cIdx) => {
    if (isLongPress.current) {
      isLongPress.current = false;
      return;
    }
    if (isVerified || !cellDto.coveredColumns) return;
    const isLeaf = (rIdx + (cellDto.rowSpan || 1)) >= (file.headerGrid?.length || 1);
    const cellKey = `${rIdx}_${cIdx}`;
    if (!isLeaf) {
      setExcludedGridCells(prev => ({ ...prev, [cellKey]: !prev[cellKey] }));
      return;
    }
    const allSelected = isGridHeaderSelected(cellDto, cellKey);
    setMappings(prev => {
      const next = { ...prev };
      cellDto.coveredColumns.forEach(colIdx => {
        const h = headers[colIdx];
        if (next[h]) {
          next[h] = { ...next[h], selected: !allSelected };
        }
      });
      return next;
    });
  };

  const getHeaderClass = (colName) => {
    if (isColSelected(colName)) return 'bg-orange-200 border-orange-400 text-orange-900 cursor-pointer shadow-inner';
    return 'bg-gray-100 text-gray-400 opacity-60 cursor-pointer hover:bg-orange-50';
  };

  const getGridHeaderClass = (cellDto, cellKey) => {
    if (isGridHeaderSelected(cellDto, cellKey)) return 'bg-orange-200 border-orange-400 text-orange-900 cursor-pointer shadow-inner font-medium';
    return 'bg-gray-100 text-gray-400 opacity-60 cursor-pointer hover:bg-orange-50';
  };

  const getDataClass = (colName) => {
    if (isColSelected(colName)) return 'bg-orange-50 text-orange-900 font-medium';
    return 'bg-gray-50 text-gray-400 opacity-50';
  };

  const handleVerify = () => {
    // Chỉ lấy những cột được selected, truyền lên dạng { TênGốc: TênMới }
    const finalMappings = {};
    Object.keys(mappings).forEach(k => {
      if (mappings[k].selected) {
        finalMappings[k] = mappings[k].newName;
      }
    });
    onVerify(finalMappings);
  };

  const handleMouseDown = (e, colName) => {
    if (!colName) return;
    isLongPress.current = false;
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = { top: rect.bottom, left: rect.left };
    pressTimer.current = setTimeout(() => {
      isLongPress.current = true;
      setPreviewColumn(colName);
      setPreviewPosition(pos);
    }, 500); // 0.5s
  };

  const handleTouchStart = (e, colName) => {
    if (!colName) return;
    isLongPress.current = false;
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = { top: rect.bottom, left: rect.left };
    pressTimer.current = setTimeout(() => {
      isLongPress.current = true;
      setPreviewColumn(colName);
      setPreviewPosition(pos);
    }, 500);
  };

  const handleMouseUp = () => {
    if (pressTimer.current) {
      clearTimeout(pressTimer.current);
      pressTimer.current = null;
    }
    setPreviewColumn(null);
  };

  // Cleanup timer on unmount and catch global mouseup
  useEffect(() => {
    const onUp = () => {
      if (pressTimer.current) {
        clearTimeout(pressTimer.current);
        pressTimer.current = null;
      }
      setPreviewColumn(null);
    };
    window.addEventListener('mouseup', onUp);
    window.addEventListener('touchend', onUp);
    return () => {
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchend', onUp);
      if (pressTimer.current) clearTimeout(pressTimer.current);
    };
  }, []);

  // Auto-scroll to preview column
  useEffect(() => {
    if (previewColumn && viewMode === 'mapping') {
      // Find the highlighted column header
      const el = document.querySelector('.outline-red-500');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    }
  }, [previewColumn, viewMode]);

  return (
    <>
      {/* Backdrop for fullscreen mode */}
      {isExpanded && (
        <div className="fixed inset-0 bg-slate-900/50 z-40 backdrop-blur-sm" onClick={() => setIsExpanded(false)} />
      )}
      


      <div className={`bg-white rounded-xl border ${isVerified ? 'border-green-400 shadow-md shadow-green-50' : 'border-gray-200 shadow-sm'} overflow-hidden flex flex-col transition-all duration-300 ${
        isExpanded 
          ? 'fixed inset-4 md:inset-10 z-50 shadow-2xl' 
          : 'h-[480px] relative'
      }`}>
      
      {/* Header card */}
      <div className="bg-gray-50 border-b border-gray-200 p-3 flex justify-between items-center h-[52px]">
        <div className="flex items-center space-x-2 text-blue-700 font-semibold min-w-0 flex-1 pr-4">
          <FileText size={18} className="flex-shrink-0" />
          <span className="truncate" title={file.fileName}>{file.fileName}</span>
        </div>
        <div className="flex items-center space-x-2 text-sm flex-shrink-0">
          <button 
            onClick={() => setViewMode(viewMode === 'table' ? 'mapping' : 'table')}
            className="flex items-center space-x-1 px-2.5 py-1 text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-100 transition-colors font-medium shadow-sm"
            title={viewMode === 'table' ? 'Chuyển sang danh sách cột để đổi tên' : 'Chuyển sang xem trước bảng Excel'}
          >
            <Eye size={14} className="text-gray-500" />
            <span>{viewMode === 'table' ? 'Đổi tên cột' : 'Xem dạng bảng'}</span>
          </button>
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-1 px-2 py-1 text-blue-600 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition-colors font-medium"
          >
            {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />} 
            <span>{isExpanded ? 'Thu nhỏ' : 'Phóng to'}</span>
          </button>
          <button className="flex items-center space-x-1 px-2 py-1 text-gray-500 bg-white border border-gray-300 rounded hover:bg-gray-100 transition-colors hidden sm:flex">
            <RefreshCcw size={14} /> <span>Dò lại</span>
          </button>
        </div>
      </div>

      {/* Cấu hình sheet & header */}
      <div className="p-3 bg-white border-b border-gray-200 flex flex-col sm:flex-row sm:items-center gap-4 text-sm text-gray-700">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <label className="font-medium">Sheet:</label>
            <select 
              value={file.selectedSheet || ''} 
              onChange={(e) => onSheetChange && onSheetChange(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1 bg-white text-gray-700 cursor-pointer shadow-sm hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
              disabled={isVerified || !file.sheetNames || file.sheetNames.length <= 1}
            >
              {file.sheetNames && file.sheetNames.length > 0 ? (
                file.sheetNames.map((s, i) => <option key={i} value={s}>{s}</option>)
              ) : (
                <option value="">Sheet 1 (Mặc định)</option>
              )}
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <label className="font-medium">Dòng header:</label>
            <input 
              type="number" 
              value={headerRowIndex} 
              onChange={(e) => setHeaderRowIndex(parseInt(e.target.value) || 0)}
              className="border border-gray-300 rounded px-2 py-1 w-16 text-center"
              min={0}
              max={5}
              disabled={isVerified}
            />
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden relative select-none flex flex-col bg-gray-100">
        {loading || !mappings ? (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 z-30">
            <span className="animate-spin text-2xl">⏳</span>
            <span className="ml-2 text-gray-600 font-medium">Đang tải preview...</span>
          </div>
        ) : error ? (
          <div className="absolute inset-0 flex items-center justify-center text-red-500 z-30">{error}</div>
        ) : data.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 z-30">File không có dữ liệu</div>
        ) : (
          <>
            {viewMode === 'mapping' && (
              <div className="absolute inset-0 flex flex-col bg-white">
            <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-gray-50/50">
              <div className="flex items-center space-x-3 px-2 py-1 text-xs font-bold text-gray-500 uppercase tracking-wider">
                <div className="w-8 text-center">Giữ</div>
                <div className="w-1/3">Tên cột gốc</div>
                <div className="w-8"></div>
                <div className="flex-1">Tên cột sẽ được map sang</div>
              </div>
              {headers.map((h, idx) => (
                <div key={idx} className={`flex items-center space-x-3 p-2 rounded-lg border transition-colors ${mappings[h]?.selected ? 'bg-white border-blue-200 shadow-sm' : 'bg-gray-100 border-gray-200 opacity-60 hover:opacity-100'}`}>
                  <div className="w-8 flex justify-center">
                    <input 
                      type="checkbox" 
                      checked={mappings[h]?.selected || false} 
                      onChange={() => toggleColumn(h)}
                      disabled={isVerified}
                      className="w-4 h-4 accent-blue-600 cursor-pointer"
                    />
                  </div>
                  <div 
                    className="w-1/3 truncate text-sm font-medium text-gray-700 cursor-help select-none" 
                    title={`Nhấn giữ để xem dữ liệu cột ${h}`}
                    onMouseDown={(e) => handleMouseDown(e, h)}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    onTouchStart={(e) => handleTouchStart(e, h)}
                    onTouchEnd={handleMouseUp}
                  >
                    {h}
                  </div>
                  <div className="text-gray-400 w-8 text-center">→</div>
                  <input
                    type="text"
                    value={mappings[h]?.newName || ''}
                    onChange={(e) => {
                      const val = e.target.value;
                      setMappings(prev => ({
                        ...prev,
                        [h]: { ...prev[h], newName: val }
                      }));
                    }}
                    disabled={!mappings[h]?.selected || isVerified}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500 transition-colors"
                    placeholder="Nhập tên mới..."
                  />
                </div>
              ))}
            </div>
          </div>
          )}
          {(viewMode === 'table' || previewColumn) && (
          <div className={`absolute inset-0 overflow-auto bg-white ${previewColumn && viewMode === 'mapping' ? 'z-50 pointer-events-none' : ''}`}>
          <table className="min-w-full border-collapse bg-white text-xs whitespace-nowrap">
            <thead className="sticky top-0 z-20 shadow-sm">
              <tr className="bg-[#e6e6e6]">
                <th className="border border-gray-300 w-10 text-center font-normal text-gray-500 bg-[#e6e6e6]"></th>
                {headers.map((h, idx) => (
                  <th 
                    key={`col-${idx}`} 
                    onClick={() => toggleColumn(h)}
                    onMouseDown={(e) => handleMouseDown(e, h)}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    onTouchStart={(e) => handleTouchStart(e, h)}
                    onTouchEnd={handleMouseUp}
                    className={`border border-gray-300 px-3 py-1 font-normal text-center min-w-[100px] transition-colors cursor-pointer ${isColSelected(h) ? 'bg-orange-300 text-orange-900 font-semibold' : 'text-gray-700 hover:bg-orange-200'} ${h === previewColumn ? 'bg-red-200 text-red-900 font-bold outline outline-2 outline-red-500 -outline-offset-2' : ''}`}
                  >
                    {getColumnLetter(idx)}
                  </th>
                ))}
              </tr>
              
              {file.headerGrid && file.headerGrid.length > 0 ? (
                file.headerGrid.map((row, rIdx) => (
                  <tr key={`hrow-${rIdx}`} className="bg-white">
                    {rIdx === 0 && (
                      <th 
                        rowSpan={file.headerGrid.length} 
                        className={`border border-gray-300 w-10 text-center text-gray-500 bg-[#e6e6e6] font-medium sticky left-0 z-30 cursor-help ${headers[0] === previewColumn ? 'bg-red-100 text-red-900 outline outline-2 outline-red-500 -outline-offset-2 font-bold' : ''}`}
                        title="Nhấn giữ để xem dữ liệu cột đầu tiên"
                        onMouseDown={(e) => handleMouseDown(e, headers[0])}
                        onMouseUp={handleMouseUp}
                        onMouseLeave={handleMouseUp}
                        onTouchStart={(e) => handleTouchStart(e, headers[0])}
                        onTouchEnd={handleMouseUp}
                      >
                        STT
                      </th>
                    )}
                    {row.map((cell, cIdx) => {
                      const leafCol = cell.coveredColumns?.[0];
                      const targetHeader = leafCol !== undefined ? headers[leafCol] : cell.text;
                      return (
                      <th 
                        key={`hcell-${rIdx}-${cIdx}`}
                        colSpan={cell.colSpan}
                        rowSpan={cell.rowSpan}
                        onClick={() => handleGridHeaderClick(cell, rIdx, cIdx)}
                        onMouseDown={(e) => handleMouseDown(e, targetHeader)}
                        onMouseUp={handleMouseUp}
                        onMouseLeave={handleMouseUp}
                        onTouchStart={(e) => handleTouchStart(e, targetHeader)}
                        onTouchEnd={handleMouseUp}
                        className={`border border-gray-300 px-3 py-2 transition-colors ${getGridHeaderClass(cell, `${rIdx}_${cIdx}`)}`}
                        title={(() => {
                          if (leafCol !== undefined && mappings?.[headers[leafCol]]) {
                            return `Tên chuẩn hóa: "${mappings[headers[leafCol]].newName}" (Nhấn giữ để xem dữ liệu mẫu)`;
                          }
                          return `${cell.text} (Nhấn giữ để xem dữ liệu mẫu)`;
                        })()}
                      >
                        {cell.text}
                      </th>
                    );})}
                  </tr>
                ))
              ) : (
                <tr className="bg-white">
                  <th 
                    className={`border border-gray-300 w-10 text-center text-gray-500 bg-[#e6e6e6] font-medium sticky left-0 z-30 cursor-help ${headers[0] === previewColumn ? 'bg-red-100 text-red-900 outline outline-2 outline-red-500 -outline-offset-2 font-bold' : ''}`}
                    title="Nhấn giữ để xem dữ liệu"
                    onMouseDown={(e) => handleMouseDown(e, headers[0])}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    onTouchStart={(e) => handleTouchStart(e, headers[0])}
                    onTouchEnd={handleMouseUp}
                  >STT</th>
                  {headers.map((h, idx) => (
                    <th 
                      key={`h-${idx}`} 
                      onClick={() => toggleColumn(h)}
                      onMouseDown={(e) => handleMouseDown(e, h)}
                      onMouseUp={handleMouseUp}
                      onMouseLeave={handleMouseUp}
                      onTouchStart={(e) => handleTouchStart(e, h)}
                      onTouchEnd={handleMouseUp}
                      className={`border border-gray-300 px-3 py-2 transition-colors font-medium ${getHeaderClass(h)} ${h === previewColumn ? 'bg-red-100 text-red-900 outline outline-2 outline-red-500 -outline-offset-2 font-bold' : ''}`}
                    >
                      <div className="flex items-center justify-between group">
                        <span className="flex-1" title="Tên cột đã map">{mappings[h]?.newName}</span>
                      </div>
                    </th>
                  ))}
                </tr>
              )}
            </thead>
            <tbody>
              {data.map((row, rIdx) => (
                <tr key={rIdx}>
                  <td className="border border-gray-300 w-10 text-center text-gray-500 bg-[#e6e6e6] sticky left-0 z-10">{rIdx + 2}</td>
                  {headers.map((h, cIdx) => (
                    <td 
                      key={cIdx} 
                      className={`border border-gray-300 px-3 py-1 truncate max-w-[200px] transition-colors ${getDataClass(h)} ${h === previewColumn ? 'bg-red-50/80 font-medium text-red-900 outline outline-2 outline-red-500/50 -outline-offset-2' : ''}`} 
                      title={row[h] !== null && row[h] !== undefined ? String(row[h]) : ''}
                    >
                      {row[h] !== null && row[h] !== undefined ? String(row[h]) : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          </div>
            )}
          </>
        )}
      </div>

      {/* Footer / Xác nhận */}
      <div className="p-3 bg-gray-50 border-t border-gray-200 flex justify-between items-center z-10 relative">
        {!isVerified ? (
          <button 
            onClick={handleVerify}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm"
          >
            <span>✔ Xác nhận cấu trúc file này</span>
          </button>
        ) : (
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-50 text-green-700 border border-green-200 rounded-lg font-medium">
            <CheckCircle size={18} />
            <span>Đã xác nhận cấu trúc</span>
          </div>
        )}
        {isVerified && (
          <button 
            onClick={() => onVerify(null)} 
            className="text-xs text-blue-600 hover:underline"
          >
            Sửa lại
          </button>
        )}
      </div>
    </div>
    </>
  );
}
