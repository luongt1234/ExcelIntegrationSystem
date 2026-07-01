import React, { useState, useEffect, useMemo } from 'react';
import { Download, RefreshCw, ArrowUpDown, ArrowUp, ArrowDown, CheckSquare, Square, RotateCcw } from 'lucide-react';
import FileUploader from '../components/FileUploader/FileUploader';
import { previewUnpivot, exportUnpivotResult, downloadBlob, getFileData, getFileStructure } from '../services/excelService';
import { useAppContext } from '../contexts/AppContext';

// ── Các bước trong luồng Unpivot ───────────────────────────────────────
const STEPS = ['Tải File', 'Chọn Cột', 'Kết Quả'];

export default function Unpivot() {
  const { unpivotState, setUnpivotState, resetUnpivotState, setHeaderCenterContent } = useAppContext();
  const {
    step,
    uploadedFile,
    allHeaders,
    unpivotColumns,
    attributeColumnName,
    valueColumnName,
    includeValueColumn,
    skipEmptyValues,
    previewResult,
  } = unpivotState;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('desc');
  const [previewData, setPreviewData] = useState([]);

  const setStep = React.useCallback((v) =>
    setUnpivotState(p => ({ ...p, step: typeof v === 'function' ? v(p.step) : v })),
    [setUnpivotState]
  );
  const updateState = (updates) => setUnpivotState(prev => ({ ...prev, ...updates }));

  // ── Stepper trong Header ─────────────────────────────────────────────
  useEffect(() => {
    setHeaderCenterContent(
      <div className="flex justify-between items-center relative w-full max-w-[450px] h-8">
        <div className="absolute top-1/2 -translate-y-1/2 left-[16.67%] right-[16.67%] h-[2px] bg-gray-100 z-0" />
        <div
          className="absolute top-1/2 -translate-y-1/2 left-[16.67%] h-[2px] bg-purple-500 z-0 transition-all duration-500"
          style={{ width: `${step * 33.33}%` }}
        />
        {STEPS.map((s, i) => (
          <div
            key={i}
            onClick={() => i < step ? setStep(i) : null}
            className={`flex flex-col items-center justify-center relative flex-1 z-10 transition-all group ${
              i <= step ? 'text-purple-600' : 'text-gray-400'
            } ${i < step ? 'cursor-pointer' : ''}`}
            title={i < step ? 'Click để quay lại bước này' : ''}
          >
            <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-[11px] transition-all duration-300 bg-white ${
              i < step ? 'bg-purple-600 text-white shadow-sm ring-2 ring-purple-100 group-hover:bg-purple-700' :
              i === step ? 'bg-white text-purple-600 ring-4 ring-purple-100' :
              'bg-white text-gray-300 ring-2 ring-gray-100'
            }`}>
              {i < step ? '✔' : i + 1}
            </div>
            <span className={`absolute top-[120%] left-1/2 -translate-x-1/2 w-[140%] text-[9px] uppercase tracking-wider text-center leading-tight transition-all duration-300 ${i === step ? 'font-bold' : 'font-medium'}`}>{s}</span>
          </div>
        ))}
      </div>
    );
    return () => setHeaderCenterContent(null);
  }, [step, setStep, setHeaderCenterContent]);

  // ── Tải dữ liệu preview file ở bước 1 ───────────────────────────────
  useEffect(() => {
    if (!uploadedFile) { setPreviewData([]); return; }
    let mounted = true;
    getFileData(uploadedFile.fileId, uploadedFile.selectedSheet)
      .then(res => { if (mounted) setPreviewData((res.data || []).slice(0, 8)); })
      .catch(() => { if (mounted) setPreviewData([]); });
    return () => { mounted = false; };
  }, [uploadedFile?.fileId, uploadedFile?.selectedSheet]);

  // ── Upload file xong → lưu state → chuyển bước ──────────────────────
  const handleUploadSuccess = (fileData) => {
    updateState({
      uploadedFile: fileData,
      allHeaders: fileData.headers || [],
      unpivotColumns: [],
      previewResult: null,
    });
    setStep(1);
  };

  const handleSheetChange = async (newSheetName) => {
    if (!uploadedFile || uploadedFile.selectedSheet === newSheetName) return;
    setLoading(true);
    setError('');
    try {
      const res = await getFileStructure(uploadedFile.fileId, newSheetName);
      updateState({
        uploadedFile: { ...res.data, fileId: res.data.filePath, fileName: uploadedFile.fileName || uploadedFile.name },
        allHeaders: res.data.headers || [],
        unpivotColumns: [],
        previewResult: null,
      });
    } catch (err) {
      setError('Lỗi khi đổi sheet: ' + (err.response?.data || err.message));
    } finally {
      setLoading(false);
    }
  };

  // ── Toggle chọn/bỏ chọn cột Unpivot ─────────────────────────────────
  const toggleColumn = (h) => {
    const next = unpivotColumns.includes(h)
      ? unpivotColumns.filter(c => c !== h)
      : [...unpivotColumns, h];
    updateState({ unpivotColumns: next });
  };

  const selectAll = () => updateState({ unpivotColumns: [...allHeaders] });
  const clearAll  = () => updateState({ unpivotColumns: [] });

  // ── Gọi preview ──────────────────────────────────────────────────────
  const handlePreview = async () => {
    if (unpivotColumns.length === 0) {
      setError('Vui lòng chọn ít nhất 1 cột cần thu gọn.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await previewUnpivot({
        fileId: uploadedFile.fileId,
        sheetName: uploadedFile.selectedSheet || null,
        unpivotColumns,
        attributeColumnName,
        valueColumnName,
        includeValueColumn,
        skipEmptyValues,
      });
      updateState({ previewResult: res.data });
      setStep(2);
    } catch (e) {
      setError(e.response?.data || 'Có lỗi xảy ra khi tạo xem trước.');
    } finally {
      setLoading(false);
    }
  };

  // ── Xuất Excel ───────────────────────────────────────────────────────
  const handleExport = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await exportUnpivotResult({
        fileId: uploadedFile.fileId,
        sheetName: uploadedFile.selectedSheet || null,
        unpivotColumns,
        attributeColumnName,
        valueColumnName,
        includeValueColumn,
        skipEmptyValues,
      });
      downloadBlob(res, 'KetQua_ChuyenDoiNgangDoc.xlsx');
    } catch {
      setError('Có lỗi khi xuất file.');
    } finally {
      setLoading(false);
    }
  };

  // ── Sắp xếp bảng kết quả ─────────────────────────────────────────────
  const handleSortColumn = (col) => {
    if (sortColumn !== col) { setSortColumn(col); setSortDirection('desc'); }
    else if (sortDirection === 'desc') setSortDirection('asc');
    else setSortColumn(null);
  };

  const sortedRows = useMemo(() => {
    if (!previewResult?.previewRows) return [];
    if (!sortColumn) return previewResult.previewRows;
    return [...previewResult.previewRows].sort((a, b) => {
      const va = a[sortColumn]; const vb = b[sortColumn];
      const ha = va != null && va !== ''; const hb = vb != null && vb !== '';
      if (ha && !hb) return sortDirection === 'desc' ? -1 : 1;
      if (!ha && hb) return sortDirection === 'desc' ? 1 : -1;
      if (va === vb) return 0;
      return sortDirection === 'asc'
        ? String(va).localeCompare(String(vb), 'vi')
        : String(vb).localeCompare(String(va), 'vi');
    });
  }, [previewResult?.previewRows, sortColumn, sortDirection]);

  // Cột kết quả (attributeCol + valueCol)
  const resultCols = previewResult
    ? [attributeColumnName, includeValueColumn ? valueColumnName : null].filter(Boolean).filter(c => previewResult.headers.includes(c))
    : [];

  // ── RENDER ───────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-base font-semibold text-gray-800">
            {step === 0 ? 'Bước 1 — Tải File' : step === 1 ? 'Bước 2 — Chọn Cột Cần Thu Gọn' : 'Bước 3 — Xem trước & Xuất file'}
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">Chuyển đổi nhiều cột nằm ngang thành dạng cột dọc (Unpivot / Melt)</p>
        </div>
        <div className="flex items-center gap-2">
          {step > 0 && (
            <button onClick={() => setStep(s => s - 1)} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors cursor-pointer">
              ← Quay lại
            </button>
          )}
          <button onClick={() => { resetUnpivotState(); setSortColumn(null); }} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors flex items-center gap-1.5">
            <RotateCcw size={14} /> Bắt đầu lại
          </button>
          {step === 2 && previewResult && (
            <button onClick={handleExport} disabled={loading} className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2">
              <Download size={15} />
              <span>Xuất Excel</span>
            </button>
          )}
        </div>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-100">⚠️ {error}</p>}

      {/* BƯỚC 0: Upload */}
      {step === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <FileUploader
            initialFile={uploadedFile}
            onUploadSuccess={handleUploadSuccess}
            onSheetChange={handleSheetChange}
            onRemove={() => updateState({ uploadedFile: null, allHeaders: [], unpivotColumns: [], previewResult: null })}
          />
        </div>
      )}

      {/* BƯỚC 1: Chọn cột */}
      {step === 1 && uploadedFile && (
        <div className="space-y-4">
          {/* Cấu hình tên cột + bỏ dòng rỗng */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Cấu hình kết quả sau khi thu gọn</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-start">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Tên cột Danh mục <span className="text-purple-600 font-semibold">*</span> <span className="text-gray-400">(chứa tên cột gốc)</span>
                </label>
                <input
                  type="text"
                  value={attributeColumnName}
                  onChange={e => updateState({ attributeColumnName: e.target.value })}
                  className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-400 font-medium"
                  placeholder="Ví dụ: Phân loại, Danh mục..."
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-gray-600">
                    Tên cột Giá trị <span className="text-gray-400">(chứa dữ liệu ô)</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer select-none text-xs text-purple-600 font-semibold hover:text-purple-700">
                    <input
                      type="checkbox"
                      checked={includeValueColumn}
                      onChange={e => updateState({ includeValueColumn: e.target.checked })}
                      className="w-3.5 h-3.5 accent-purple-600 rounded"
                    />
                    <span>Kèm cột này</span>
                  </label>
                </div>
                {includeValueColumn ? (
                  <input
                    type="text"
                    value={valueColumnName}
                    onChange={e => updateState({ valueColumnName: e.target.value })}
                    className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-400 font-medium"
                    placeholder="Ví dụ: Giá trị..."
                  />
                ) : (
                  <div className="w-full px-3 py-1.5 bg-gray-100 border border-gray-200 rounded-lg text-xs text-gray-400 italic flex items-center h-[34px]">
                    Đã tắt (chỉ xuất cột Danh mục)
                  </div>
                )}
              </div>
              <div className="pt-6">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={skipEmptyValues}
                    onChange={e => updateState({ skipEmptyValues: e.target.checked })}
                    className="w-4 h-4 accent-purple-600 rounded"
                  />
                  <span className="text-sm text-gray-700 font-medium">Bỏ qua dòng giá trị rỗng</span>
                </label>
              </div>
            </div>
          </div>

          {/* Bảng dữ liệu gốc kiêm chọn cột */}
          {allHeaders.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                    <span>Chọn cột cần thu gọn trực tiếp trên bảng dữ liệu</span>
                    <span className="font-normal text-gray-400 text-xs">({previewData.length || 0} dòng mẫu)</span>
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Nhấn vào tiêu đề cột hoặc ô dữ liệu bên dưới để <span className="font-medium text-purple-600">chọn/bỏ chọn</span> cột cần thu gọn thành dòng.
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  {uploadedFile.sheetNames && uploadedFile.sheetNames.length > 0 && (
                    <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-gray-300 shadow-2xs">
                      <span className="text-xs font-semibold text-gray-600">Sheet:</span>
                      <select
                        value={uploadedFile.selectedSheet || ''}
                        onChange={(e) => handleSheetChange(e.target.value)}
                        disabled={loading}
                        className="text-xs font-bold text-purple-700 bg-transparent border-none focus:outline-none cursor-pointer pr-1"
                      >
                        {uploadedFile.sheetNames.map((s, idx) => (
                          <option key={idx} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                  )}
                  <span className="text-xs font-medium text-gray-600">{unpivotColumns.length}/{allHeaders.length} cột</span>
                  <button onClick={selectAll} className="px-2.5 py-1 text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors font-medium cursor-pointer">Chọn tất cả</button>
                  <button onClick={clearAll} className="px-2.5 py-1 text-xs bg-gray-50 text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors font-medium cursor-pointer">Bỏ chọn</button>
                </div>
              </div>
              <div className="overflow-x-auto max-h-[500px]">
                <table className="w-full text-left border-collapse text-xs whitespace-nowrap">
                  <thead>
                    <tr className="bg-gray-100 text-gray-600 font-semibold uppercase border-b border-gray-200 sticky top-0 z-10">
                      <th className="py-2 px-3 w-10 text-center bg-gray-200/90 border-r border-gray-300 sticky left-0 z-20">STT</th>
                      {allHeaders.map((h, idx) => {
                        const isSelected = unpivotColumns.includes(h);
                        return (
                          <th key={idx} onClick={() => toggleColumn(h)}
                            className={`py-2 px-3 cursor-pointer transition-colors ${isSelected ? 'bg-purple-100 text-purple-900 font-bold border-x border-purple-200' : 'hover:bg-purple-50'}`}>
                            <div className="flex items-center gap-1">
                              {isSelected ? <CheckSquare size={12} className="text-purple-500 shrink-0" /> : <Square size={12} className="text-gray-400 shrink-0" />}
                              {h}
                            </div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {previewData.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-gray-50/80">
                        <td className="py-1.5 px-3 text-center text-gray-500 bg-gray-100/80 border-r border-gray-200 sticky left-0 font-semibold">{rIdx + 1}</td>
                        {allHeaders.map((h, cIdx) => {
                          const val = row[h];
                          const isSelected = unpivotColumns.includes(h);
                          return (
                            <td key={cIdx} onClick={() => toggleColumn(h)}
                              className={`py-1.5 px-3 cursor-pointer ${isSelected ? 'bg-purple-50/60 text-purple-900 border-x border-purple-100/60' : 'text-gray-700'}`}>
                              {val != null ? String(val) : ''}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Nút tiếp theo */}
          <div className="flex justify-end">
            <button
              onClick={handlePreview}
              disabled={loading || unpivotColumns.length === 0}
              className="px-6 py-2.5 bg-purple-600 text-white rounded-lg text-sm font-semibold hover:bg-purple-700 transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? <RefreshCw size={15} className="animate-spin" /> : null}
              Xem trước kết quả →
            </button>
          </div>
        </div>
      )}

      {/* BƯỚC 2: Kết quả */}
      {step === 2 && previewResult && (
        <div className="space-y-4">
          {/* Stats bar */}
          <div className="bg-gray-50 rounded-xl p-3 border border-gray-200/80 shadow-2xs flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-1.5 text-sm">
              <span className="text-gray-500 font-medium">Tổng dòng kết quả:</span>
              <span className="font-bold text-purple-600 text-base">{previewResult.totalRows?.toLocaleString()}</span>
            </div>
            <div className="w-px h-4 bg-gray-300 hidden sm:block" />
            <div className="flex items-center gap-1.5 text-sm">
              <span className="text-gray-500 font-medium">Số cột:</span>
              <span className="font-bold text-orange-600 text-base">{previewResult.headers.length}</span>
            </div>
            <div className="w-px h-4 bg-gray-300 hidden sm:block" />
            <div className="flex items-center gap-1.5 text-sm">
              <span className="text-gray-500 font-medium">Cột đã unpivot:</span>
              <span className="font-bold text-green-600 text-base">{unpivotColumns.length}</span>
            </div>
            {Object.keys(previewResult.columnStats).length > 0 && (
              <>
                <div className="w-px h-4 bg-gray-300 hidden sm:block" />
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-xs font-semibold text-gray-500 mr-1">Số dòng/cột:</span>
                  {Object.entries(previewResult.columnStats).map(([col, count], i) => (
                    <span key={i} className="inline-flex items-center gap-1 bg-white px-2 py-0.5 rounded-md border border-gray-200/80 text-xs shadow-2xs">
                      <span className="font-medium text-gray-700 max-w-[100px] truncate" title={col}>{col}:</span>
                      <span className="font-bold text-purple-600 bg-purple-50/80 px-1 rounded">{count}</span>
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Bảng kết quả */}
          <div className="rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex items-center gap-2">
              <h3 className="font-semibold text-gray-800 text-sm flex items-center gap-2">
                Xem trước dữ liệu (15 dòng đầu)
                <span className="font-normal text-purple-600 text-xs bg-purple-50 px-2 py-0.5 rounded-md border border-purple-100">💡 Nhấn tiêu đề cột để sắp xếp</span>
              </h3>
            </div>
            <div className="overflow-x-auto max-h-[560px]">
              <table className="w-full text-left border-collapse text-sm whitespace-nowrap">
                <thead>
                  <tr className="bg-gray-100 text-gray-600 text-xs font-semibold uppercase border-b border-gray-200 sticky top-0 z-10">
                    <th className="py-2.5 px-3 w-12 text-center bg-gray-200/90 text-gray-700 font-bold border-r border-gray-300 sticky left-0 z-20 shadow-2xs">STT</th>
                    {previewResult.headers.map((h, idx) => {
                      const isResult = resultCols.includes(h);
                      const isSorted = sortColumn === h;
                      return (
                        <th key={idx} onClick={() => handleSortColumn(h)}
                          className={`py-2.5 px-4 cursor-pointer select-none transition-colors hover:bg-purple-100/80 group ${
                            isResult ? 'bg-purple-50/40 text-purple-900 font-bold border-x border-purple-100' : ''
                          } ${isSorted ? '!bg-purple-100 text-purple-950 shadow-inner' : ''}`}>
                          <div className="flex items-center justify-between gap-1.5">
                            <span>{h}</span>
                            {isSorted
                              ? sortDirection === 'desc' ? <ArrowDown size={14} className="text-purple-600 shrink-0" /> : <ArrowUp size={14} className="text-purple-600 shrink-0" />
                              : <ArrowUpDown size={12} className="text-gray-400 opacity-40 group-hover:opacity-100 shrink-0 transition-opacity" />}
                          </div>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {sortedRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-2.5 px-3 text-center text-xs font-semibold text-gray-600 bg-gray-100/90 border-r border-gray-200 sticky left-0 z-10 select-none shadow-2xs">{rIdx + 1}</td>
                      {previewResult.headers.map((h, cIdx) => {
                        const val = row[h];
                        const isResult = resultCols.includes(h);
                        return (
                          <td key={cIdx} className={`py-2.5 px-4 ${isResult ? 'text-center border-x border-purple-100/60 bg-purple-50/10 font-medium text-purple-900' : 'text-gray-700'}`}>
                            {val != null && val !== undefined ? String(val) : ''}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
