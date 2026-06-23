import React, { useEffect, useState } from 'react';
import { FileText, Eye, CheckCircle, RefreshCcw, Maximize2, Minimize2, Settings2 } from 'lucide-react';
import { getFileData } from '../services/excelService';
import { hrDictionaries, getStandardizedColumnName } from '../utils/hrDictionary';

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
  const [editingCol, setEditingCol] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [viewMode, setViewMode] = useState('data'); // 'data' | 'mapping'

  const [previewColumn, setPreviewColumn] = useState(null);
  const [previewPosition, setPreviewPosition] = useState({ top: 0, left: 0 });
  const pressTimer = React.useRef(null);

  const [ignoredHeaderCells, setIgnoredHeaderCells] = useState(new Set());

  const headers = file.headers?.length > 0 
    ? file.headers 
    : (data.length > 0 ? Object.keys(data[0]) : []);

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
          loadedHeaders.forEach(h => {
            const defaultNewName = suggestedMappings[h] || h;
            initialMappings[h] = { newName: defaultNewName, selected: true };
          });
          setMappings(initialMappings);
          setIgnoredHeaderCells(new Set()); // Reset ignored cells on load
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

  // Effect to rebuild newName when ignoredHeaderCells changes
  useEffect(() => {
    if (!file.headerGrid || file.headerGrid.length === 0 || !mappings) return;

    setMappings(prev => {
      const next = { ...prev };
      let changed = false;
      
      headers.forEach((h, colIdx) => {
        const parts = [];
        file.headerGrid.forEach((row, rIdx) => {
          const cIdx = row.findIndex(c => c.coveredColumns.includes(colIdx));
          if (cIdx !== -1) {
            const cellKey = `${rIdx}-${cIdx}`;
            const cell = row[cIdx];
            if (!ignoredHeaderCells.has(cellKey) && cell.text && cell.text.trim() !== '') {
              if (parts.length === 0 || parts[parts.length - 1] !== cell.text) {
                parts.push(cell.text);
              }
            }
          }
        });
        
        const generatedName = parts.join(' - ');
        let finalName = generatedName || h;
        
        // Import getStandardizedColumnName is already at the top? Wait, I need to make sure. I will import it if needed.
        // Actually, I'll assume we can use the auto-mapping from suggestedMappings or apply it manually.
        // Let's use hrDictionaries to standardize if possible.
        // I will do standardizing manually here since I have hrDictionaries imported.
        let standardizedName = getStandardizedColumnName(finalName);
        
        if (next[h] && next[h].newName !== standardizedName) {
          next[h] = { ...next[h], newName: standardizedName };
          changed = true;
        }
      });
      
      return changed ? next : prev;
    });
  }, [ignoredHeaderCells, file.headerGrid, headers]);

  const toggleColumn = (colName) => {
    if (isVerified) return;
    setMappings(prev => ({
      ...prev,
      [colName]: { ...prev[colName], selected: !prev[colName].selected }
    }));
  };

  const handleGridHeaderClick = (cellDto, rIdx, cIdx) => {
    if (isVerified) return;
    if (!cellDto.coveredColumns || cellDto.coveredColumns.length === 0) return;
    
    const cellKey = `${rIdx}-${cIdx}`;
    setIgnoredHeaderCells(prev => {
      const next = new Set(prev);
      if (next.has(cellKey)) {
        next.delete(cellKey);
      } else {
        next.add(cellKey);
      }
      return next;
    });
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

  const getHeaderClass = (colName) => {
    if (isColSelected(colName)) return 'bg-orange-200 border-orange-400 text-orange-900 cursor-pointer shadow-inner';
    return 'bg-gray-100 text-gray-400 opacity-60 cursor-pointer hover:bg-orange-50';
  };

  const getGridHeaderClass = (cellDto, rIdx, cIdx) => {
    const cellKey = `${rIdx}-${cIdx}`;
    if (ignoredHeaderCells.has(cellKey)) {
      return 'bg-gray-100 text-gray-400 line-through cursor-pointer opacity-50 hover:bg-gray-200 border-dashed';
    }
    
    if (!mappings || !cellDto.coveredColumns || cellDto.coveredColumns.length === 0) return 'bg-white text-gray-700 cursor-pointer';
    const allSelected = cellDto.coveredColumns.every(colIdx => mappings[headers[colIdx]]?.selected);
    if (allSelected) return 'bg-orange-200 border-orange-400 text-orange-900 cursor-pointer shadow-inner font-medium hover:bg-orange-300';
    
    const anySelected = cellDto.coveredColumns.some(colIdx => mappings[headers[colIdx]]?.selected);
    if (anySelected) return 'bg-orange-100 border-orange-300 text-orange-800 cursor-pointer hover:bg-orange-200';
    
    return 'bg-white text-gray-700 cursor-pointer hover:bg-orange-50';
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
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = { top: rect.bottom, left: rect.left };
    pressTimer.current = setTimeout(() => {
      setPreviewColumn(colName);
      setPreviewPosition(pos);
    }, 800); // 0.8s
  };

  const handleTouchStart = (e, colName) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = { top: rect.bottom, left: rect.left };
    pressTimer.current = setTimeout(() => {
      setPreviewColumn(colName);
      setPreviewPosition(pos);
    }, 800);
  };

  const handleMouseUp = () => {
    if (pressTimer.current) {
      clearTimeout(pressTimer.current);
      pressTimer.current = null;
    }
    setPreviewColumn(null);
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
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
      <div className="bg-gray-50 border-b border-gray-200 p-2 flex justify-between items-center h-[42px]">
        <div className="flex items-center space-x-1.5 text-blue-700 font-semibold min-w-0 flex-1 pr-3 text-sm">
          <FileText size={15} className="flex-shrink-0" />
          <span className="truncate" title={file.fileName}>{file.fileName}</span>
        </div>
        <div className="flex items-center space-x-2 flex-shrink-0">
          <div className="flex bg-gray-200/60 p-0.5 rounded-md border border-gray-300">
            <button 
              onClick={() => setViewMode('data')}
              className={`flex items-center space-x-1 px-2.5 py-0.5 text-xs font-medium rounded transition-all ${viewMode === 'data' ? 'bg-white text-blue-700 shadow-sm border border-gray-200' : 'text-gray-600 hover:text-gray-900'}`}
            >
              <Eye size={12} /> <span>Dữ liệu</span>
            </button>
            <button 
              onClick={() => setViewMode('mapping')}
              className={`flex items-center space-x-1 px-2.5 py-0.5 text-xs font-medium rounded transition-all ${viewMode === 'mapping' ? 'bg-white text-orange-700 shadow-sm border border-gray-200' : 'text-gray-600 hover:text-gray-900'}`}
            >
              <Settings2 size={12} /> <span>Mapping</span>
            </button>
          </div>
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-1 px-2 py-0.5 text-xs text-blue-600 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition-colors font-medium hidden sm:flex"
          >
            {isExpanded ? <Minimize2 size={12} /> : <Maximize2 size={12} />} 
            <span>{isExpanded ? 'Thu nhỏ' : 'Phóng to'}</span>
          </button>
        </div>
      </div>

      {/* Cấu hình sheet & header */}
      <div className="p-3 bg-white border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-sm text-gray-700">
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
        </div>
        {viewMode === 'mapping' && !isVerified && (
          <div className="flex space-x-2 flex-shrink-0">
            <button onClick={() => {
              setMappings(prev => {
                const next = {...prev};
                Object.keys(next).forEach(k => next[k].selected = true);
                return next;
              });
            }} className="px-2.5 py-1 bg-white rounded border border-blue-200 text-[11px] uppercase hover:bg-blue-100 font-bold shadow-sm text-blue-700 whitespace-nowrap">Chọn tất cả</button>
            <button onClick={() => {
              setMappings(prev => {
                const next = {...prev};
                Object.keys(next).forEach(k => next[k].selected = false);
                return next;
              });
            }} className="px-2.5 py-1 bg-white rounded border border-gray-300 text-[11px] uppercase hover:bg-gray-100 font-bold shadow-sm text-gray-600 whitespace-nowrap">Bỏ chọn hết</button>
          </div>
        )}
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
              <div className="absolute inset-0 overflow-y-scroll flex flex-col">
                {/* Header của danh sách */}
                <div className="flex bg-white px-4 py-2 border-b border-gray-200 text-xs font-medium text-gray-500 sticky top-0 z-20 shadow-sm">
                  <div className="w-10 text-center">GIỮ</div>
                  <div className="w-1/3">TÊN CỘT GỐC</div>
                  <div className="w-8"></div>
                  <div className="flex-1 uppercase">Tên cột sẽ được map sang</div>
                </div>
                
                {/* Danh sách cột */}
                <div className="flex-1 p-2 space-y-1">
                  {(() => {
                    const sortedMappingHeaders = [...headers].sort((a, b) => {
                      const isAClassified = Object.keys(hrDictionaries).includes(suggestedMappings[a] || a);
                      const isBClassified = Object.keys(hrDictionaries).includes(suggestedMappings[b] || b);
                      if (isAClassified && !isBClassified) return -1;
                      if (!isAClassified && isBClassified) return 1;
                      return headers.indexOf(a) - headers.indexOf(b);
                    });
                    
                    return sortedMappingHeaders.map((h, idx) => (
                    <div 
                      key={idx}
                      className={`flex items-center px-2 py-1.5 rounded-lg border transition-all ${
                        mappings[h]?.selected 
                          ? 'bg-white border-gray-200 shadow-sm hover:border-blue-300' 
                          : 'bg-gray-50 border-transparent opacity-60'
                      }`}
                      title={`Nhấn giữ để xem dữ liệu cột ${h}`}
                      onMouseDown={(e) => {
                        if (e.target.tagName === 'INPUT') return;
                        handleMouseDown(e, h);
                      }}
                      onMouseUp={handleMouseUp}
                      onMouseLeave={handleMouseUp}
                      onTouchStart={(e) => {
                        if (e.target.tagName === 'INPUT') return;
                        handleTouchStart(e, h);
                      }}
                      onTouchEnd={handleMouseUp}
                    >
                      <div className="w-10 flex justify-center">
                        <input 
                          type="checkbox"
                          checked={mappings[h]?.selected || false}
                          onChange={() => toggleColumn(h)}
                          disabled={isVerified}
                          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 disabled:opacity-50 cursor-pointer"
                        />
                      </div>
                      <div 
                        className="w-1/3 truncate text-sm font-medium text-gray-700 cursor-text select-text" 
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
                  ));
                  })()}
                </div>
              </div>
            )}

            {(viewMode === 'data' || previewColumn) && (
              <div className={`absolute inset-0 overflow-auto bg-white ${previewColumn && viewMode === 'mapping' ? 'z-50 pointer-events-none' : ''}`}>
              <table className="min-w-full border-collapse bg-white text-xs whitespace-nowrap">
                <thead className="sticky top-0 z-20 shadow-sm">
                  <tr className="bg-[#e6e6e6]">
                    <th className="border border-gray-300 w-10 text-center font-normal text-gray-500 bg-[#e6e6e6]"></th>
                    {headers.map((h, idx) => (
                      <th 
                        key={`col-${idx}`} 
                        onClick={() => toggleColumn(h)}
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
                          <th rowSpan={file.headerGrid.length} className="border border-gray-300 w-10 text-center text-gray-500 bg-[#e6e6e6] font-medium sticky left-0 z-30">
                            STT
                          </th>
                        )}
                        {row.map((cell, cIdx) => (
                          <th 
                            key={`hcell-${rIdx}-${cIdx}`}
                            colSpan={cell.colSpan}
                            rowSpan={cell.rowSpan}
                            onClick={() => handleGridHeaderClick(cell, rIdx, cIdx)}
                            className={`border border-gray-300 px-3 py-2 text-center align-middle transition-colors ${getGridHeaderClass(cell, rIdx, cIdx)}`}
                          >
                            {cell.text}
                          </th>
                        ))}
                      </tr>
                    ))
                  ) : (
                    <tr className="bg-white">
                      <th className="border border-gray-300 w-10 text-center text-gray-500 bg-[#e6e6e6] font-medium sticky left-0 z-30">STT</th>
                      {headers.map((h, idx) => (
                        <th 
                          key={`h-${idx}`} 
                          onClick={() => toggleColumn(h)}
                          className={`border border-gray-300 px-3 py-2 text-center align-middle transition-colors font-medium ${getHeaderClass(h)} ${h === previewColumn ? 'bg-red-100 text-red-900 outline outline-2 outline-red-500 -outline-offset-2' : ''}`}
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
