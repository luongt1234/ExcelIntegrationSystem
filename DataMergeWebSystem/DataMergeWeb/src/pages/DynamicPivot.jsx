import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Split, AlertTriangle, Download, RefreshCw, HelpCircle, Maximize2, Minimize2, FileText, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import FileUploader from '../components/FileUploader/FileUploader';
import { analyzePivot, previewPivot, exportPivotResult, downloadBlob, getFileData } from '../services/excelService';
import { useAppContext } from '../contexts/AppContext';

// ── Helper: chuyển index cột sang chữ cái Excel (A, B, C...) ──────────
const getColumnLetter = (i) => {
  let l = '';
  let t = i;
  while (t >= 0) { l = String.fromCharCode((t % 26) + 65) + l; t = Math.floor(t / 26) - 1; }
  return l;
};

// ────────────────────────────────────────────────────────────────────────
// PivotColumnPicker — bảng Excel trực quan để chọn cột cần xoay ngang
// Học theo phong cách FileStructurePreview trong PeopleMerge
// ────────────────────────────────────────────────────────────────────────
function PivotColumnPicker({ uploadedFile, sourceColumns, loading, error, onToggleColumn, onBack, onAnalyze }) {
  const [previewData, setPreviewData] = useState([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const headers = uploadedFile?.headers || [];

  // Tải 15 dòng dữ liệu mẫu để hiển thị
  useEffect(() => {
    if (!uploadedFile) { setPreviewData([]); return; }
    let mounted = true;
    setPreviewLoading(true);
    getFileData(uploadedFile.fileId, uploadedFile.selectedSheet)
      .then(res => { if (mounted) setPreviewData((res.data || []).slice(0, 15)); })
      .catch(() => { if (mounted) setPreviewData([]); })
      .finally(() => { if (mounted) setPreviewLoading(false); });
    return () => { mounted = false; };
  }, [uploadedFile?.fileId, uploadedFile?.selectedSheet]);

  const isSelected = (h) => sourceColumns.includes(h);

  const selectAll = () => headers.forEach(h => { if (!isSelected(h)) onToggleColumn(h); });
  const clearAll  = () => headers.forEach(h => { if (isSelected(h))  onToggleColumn(h); });

  return (
    <div className="space-y-4">
      {error && (
        <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-100 flex items-center gap-2">
          <AlertTriangle size={15} className="flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Bảng Excel trực quan */}
      {uploadedFile && (
        <>
          {isExpanded && (
            <div className="fixed inset-0 bg-slate-900/50 z-40 backdrop-blur-sm" onClick={() => setIsExpanded(false)} />
          )}

          <div className={`bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col transition-all duration-300 ${
            isExpanded ? 'fixed inset-4 md:inset-10 z-50 shadow-2xl' : 'h-[520px] relative'
          }`}>

            {/* Unified Minimalist Header */}
            <div className="bg-white border-b border-gray-100 px-5 py-3 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <h2 className="text-base font-bold text-gray-800">Bước 2 — Chọn (các) cột cần chuyển đổi</h2>
                {sourceColumns.length > 0 && (
                  <span className="px-2.5 py-0.5 text-xs font-semibold bg-orange-100 text-orange-700 rounded-full border border-orange-200">
                    {sourceColumns.length} cột đang chọn
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                {headers.length > 0 && (
                  <>
                    <button
                      onClick={selectAll}
                      className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-orange-300 text-orange-700 bg-orange-50 hover:bg-orange-100 transition-colors"
                    >
                      ✓ Chọn tất cả
                    </button>
                    <button
                      onClick={clearAll}
                      className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-gray-300 text-gray-600 bg-white hover:bg-gray-50 transition-colors"
                    >
                      ✕ Bỏ chọn
                    </button>
                  </>
                )}
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  {isExpanded ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
                  <span>{isExpanded ? 'Thu nhỏ' : 'Phóng to'}</span>
                </button>
                <div className="h-4 w-px bg-gray-200 mx-1 hidden sm:block" />
                <button
                  onClick={onBack}
                  className="px-3.5 py-1.5 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
                >
                  ← Quay lại
                </button>
                <button
                  onClick={onAnalyze}
                  disabled={loading || !uploadedFile || sourceColumns.length === 0}
                  className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center gap-2"
                >
                  {loading ? <><span className="animate-spin">⏳</span><span>Đang xử lý...</span></> : <span>Tiếp theo →</span>}
                </button>
              </div>
            </div>

            {/* Bảng dữ liệu */}
            <div className="flex-1 overflow-auto bg-gray-50 select-none">
              {previewLoading ? (
                <div className="h-full flex items-center justify-center text-gray-500 gap-2">
                  <span className="animate-spin text-xl">⏳</span>
                  <span className="text-sm">Đang tải dữ liệu xem trước...</span>
                </div>
              ) : (
                <table className="min-w-full border-collapse bg-white text-xs whitespace-nowrap">
                  <thead className="sticky top-0 z-20 shadow-sm">
                    {/* Hàng chữ cái cột (A, B, C...) */}
                    <tr className="bg-[#e6e6e6]">
                      <th className="border border-gray-300 w-10 text-center font-normal text-gray-500 bg-[#e6e6e6]"></th>
                      {headers.map((h, idx) => (
                        <th
                          key={idx}
                          onClick={() => onToggleColumn(h)}
                          className={`border border-gray-300 px-3 py-1 font-normal text-center min-w-[100px] transition-colors cursor-pointer ${
                            isSelected(h)
                              ? 'bg-orange-300 text-orange-900 font-semibold'
                              : 'text-gray-700 hover:bg-orange-100'
                          }`}
                        >
                          {getColumnLetter(idx)}
                        </th>
                      ))}
                    </tr>
                    {/* Hàng tên cột (tiêu đề thực tế) */}
                    <tr className="bg-white">
                      <th className="border border-gray-300 w-10 text-center text-gray-500 bg-[#e6e6e6] font-medium sticky left-0 z-10">STT</th>
                      {headers.map((h, idx) => (
                        <th
                          key={idx}
                          onClick={() => onToggleColumn(h)}
                          className={`border border-gray-300 px-3 py-2 transition-colors font-medium cursor-pointer ${
                            isSelected(h)
                              ? 'bg-orange-200 border-orange-400 text-orange-900 shadow-inner'
                              : 'bg-gray-100 text-gray-600 hover:bg-orange-50'
                          }`}
                          title={isSelected(h) ? `Bỏ chọn cột "${h}"` : `Chọn cột "${h}" để xoay ngang`}
                        >
                          <div className="flex items-center gap-1.5">
                            {isSelected(h) && (
                              <span className="w-3 h-3 rounded-full bg-orange-500 flex-shrink-0 inline-block" />
                            )}
                            <span className="truncate max-w-[120px]">{h}</span>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.length === 0 ? (
                      <tr>
                        <td colSpan={headers.length + 1} className="text-center py-10 text-gray-400">
                          File không có dữ liệu hoặc chưa tải được
                        </td>
                      </tr>
                    ) : (
                      previewData.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-yellow-50/30">
                          <td className="border border-gray-300 w-10 text-center text-gray-500 bg-[#e6e6e6] sticky left-0 z-10">{rIdx + 2}</td>
                          {headers.map((h, cIdx) => (
                            <td
                              key={cIdx}
                              onClick={() => onToggleColumn(h)}
                              className={`border border-gray-300 px-3 py-1 truncate max-w-[200px] transition-colors cursor-pointer ${
                                isSelected(h)
                                  ? 'bg-orange-50 text-orange-900 font-medium'
                                  : 'text-gray-600 hover:bg-orange-50/30'
                              }`}
                              title={row[h] !== null && row[h] !== undefined ? String(row[h]) : ''}
                            >
                              {row[h] !== null && row[h] !== undefined ? String(row[h]) : ''}
                            </td>
                          ))}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

const STEPS = ['Tải File', 'Chọn Cột', 'Cấu Hình & Gom Nhóm', 'Kết Quả'];

export default function DynamicPivot() {
  const { pivotState, setPivotState, resetPivotState, setHeaderCenterContent } = useAppContext();
  const {
    step,
    uploadedFile,
    sourceColumns,
    ignoreCase,
    multiValueSeparator,
    analysisResult,
    columnConfigs,
    markSymbol,
    placement,
    previewResult
  } = pivotState;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('desc');

  const handleSortColumn = (colName) => {
    if (sortColumn !== colName) {
      setSortColumn(colName);
      setSortDirection('desc');
    } else if (sortDirection === 'desc') {
      setSortDirection('asc');
    } else {
      setSortColumn(null);
    }
  };

  const sortedPreviewRows = useMemo(() => {
    if (!previewResult?.previewRows) return [];
    if (!sortColumn || !previewResult.headers?.includes(sortColumn)) return previewResult.previewRows;

    return [...previewResult.previewRows].sort((a, b) => {
      const valA = a[sortColumn];
      const valB = b[sortColumn];

      const hasA = valA !== null && valA !== undefined && valA !== '';
      const hasB = valB !== null && valB !== undefined && valB !== '';

      if (hasA && !hasB) return sortDirection === 'desc' ? -1 : 1;
      if (!hasA && hasB) return sortDirection === 'desc' ? 1 : -1;

      if (valA === valB) return 0;
      if (valA === null || valA === undefined || valA === '') return 1;
      if (valB === null || valB === undefined || valB === '') return -1;

      return sortDirection === 'asc'
        ? String(valA).localeCompare(String(valB), 'vi')
        : String(valB).localeCompare(String(valA), 'vi');
    });
  }, [previewResult?.previewRows, previewResult?.headers, sortColumn, sortDirection]);

  const setStep = React.useCallback((v) =>
    setPivotState(p => ({ ...p, step: typeof v === 'function' ? v(p.step) : v })),
    [setPivotState]
  );
  const updateState = (updates) => setPivotState(prev => ({ ...prev, ...updates }));

  // ── Stepper trong Header ──────────────────────────────────────────────
  useEffect(() => {
    setHeaderCenterContent(
      <div className="flex justify-between items-center relative w-full max-w-[600px] h-8">
        <div className="absolute top-1/2 -translate-y-1/2 left-[12.5%] right-[12.5%] h-[2px] bg-gray-100 z-0" />
        <div
          className="absolute top-1/2 -translate-y-1/2 left-[12.5%] h-[2px] bg-blue-500 z-0 transition-all duration-500"
          style={{ width: `${step * 25}%` }}
        />
        {STEPS.map((s, i) => (
          <div
            key={i}
            onClick={() => i < step ? setStep(i) : null}
            className={`flex flex-col items-center justify-center relative flex-1 z-10 transition-all group ${
              i <= step ? 'text-blue-600' : 'text-gray-400'
            } ${i < step ? 'cursor-pointer' : ''}`}
            title={i < step ? 'Click để quay lại bước này' : ''}
          >
            <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-[11px] transition-all duration-300 bg-white ${
              i < step ? 'bg-blue-600 text-white shadow-sm ring-2 ring-blue-100 group-hover:bg-blue-700' :
              i === step ? 'bg-white text-blue-600 ring-4 ring-blue-100' :
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

  // ── Handlers Bước 0 ───────────────────────────────────────────────────
  const handleUploadSuccess = (fileData) => {
    updateState({
      uploadedFile: fileData,
      sourceColumns: [],
      analysisResult: null,
      columnConfigs: [],
      previewResult: null,
      step: 1
    });
    setError('');
  };

  const toggleSourceColumn = (col) => {
    const exists = sourceColumns.includes(col);
    const updated = exists ? sourceColumns.filter(c => c !== col) : [...sourceColumns, col];
    updateState({ sourceColumns: updated });
  };

  const handleAnalyze = async () => {
    if (!uploadedFile) { setError('Vui lòng tải lên file Excel.'); return; }
    if (sourceColumns.length === 0) { setError('Vui lòng chọn ít nhất 1 cột cần chuyển đổi.'); return; }
    setError('');
    setLoading(true);
    try {
      const res = await analyzePivot({
        fileId: uploadedFile.fileId,
        sheetName: uploadedFile.selectedSheet,
        sourceColumns,
        ignoreCase,
        multiValueSeparator
      });
      const analysis = res.data;
      const initialConfigs = analysis.columnsAnalysis.map(colAna => ({
        sourceColumn: colAna.sourceColumn,
        mappings: colAna.uniqueValues.map(val => ({
          originalValue: val.originalValue,
          targetColumnName: val.targetColumnName,
          isSelected: val.isSelected
        })),
        emptyRowHandling: 'Ignore',
        unspecifiedColumnName: 'Chưa xác định',
        otherColumnName: 'Khác'
      }));
      updateState({ analysisResult: analysis, columnConfigs: initialConfigs });
      setStep(2);
    } catch (err) {
      setError(err.response?.data || err.message || 'Phân tích file thất bại.');
    } finally {
      setLoading(false);
    }
  };

  // ── Handlers Bước 1 ───────────────────────────────────────────────────
  const handleMappingChange = (colIndex, valIndex, field, value) => {
    const newConfigs = [...columnConfigs];
    newConfigs[colIndex].mappings[valIndex][field] = value;
    updateState({ columnConfigs: newConfigs });
  };

  const toggleSelectAll = (colIndex, selectAll) => {
    const newConfigs = [...columnConfigs];
    newConfigs[colIndex].mappings.forEach(m => m.isSelected = selectAll);
    updateState({ columnConfigs: newConfigs });
  };

  // ── Handlers Bước 2 ───────────────────────────────────────────────────
  const handleConfigChange = (colIndex, field, value) => {
    const newConfigs = [...columnConfigs];
    newConfigs[colIndex][field] = value;
    updateState({ columnConfigs: newConfigs });
  };

  const handlePreview = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await previewPivot({
        fileId: uploadedFile.fileId,
        sheetName: uploadedFile.selectedSheet,
        columnConfigs, markSymbol, placement, multiValueSeparator, ignoreCase
      });
      updateState({ previewResult: res.data });
      setStep(3);
    } catch (err) {
      setError(err.response?.data || err.message || 'Tạo xem trước thất bại.');
    } finally {
      setLoading(false);
    }
  };

  // ── Handlers Bước 3 ───────────────────────────────────────────────────
  const handlePlacementChange = async (newPlacement) => {
    updateState({ placement: newPlacement });
    setLoading(true);
    try {
      const res = await previewPivot({
        fileId: uploadedFile.fileId,
        sheetName: uploadedFile.selectedSheet,
        columnConfigs, markSymbol, placement: newPlacement, multiValueSeparator, ignoreCase
      });
      updateState({ previewResult: res.data });
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleExport = async () => {
    setLoading(true);
    try {
      const res = await exportPivotResult({
        fileId: uploadedFile.fileId,
        sheetName: uploadedFile.selectedSheet,
        columnConfigs, markSymbol, placement, multiValueSeparator, ignoreCase
      });
      downloadBlob(res, `Pivot_${uploadedFile.fileName || 'KetQua.xlsx'}`);
    } catch (err) {
      setError(err.response?.data || err.message || 'Xuất file thất bại.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto space-y-6">
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">

        {/* ──────────────────────────────────────────────────────────── */}
        {/* BƯỚC 0: TẢI FILE EXCEL                                    */}
        {/* ──────────────────────────────────────────────────────────── */}
        {step === 0 && (
          <div className="space-y-6 max-w-2xl mx-auto py-6">
            <div className="text-center space-y-1.5">
              <h2 className="text-lg font-bold text-gray-800">Bước 1 — Tải lên file Excel đầu vào</h2>
              <p className="text-sm text-gray-500">Vui lòng chọn hoặc kéo thả file Excel chứa danh sách cần chuyển đổi dọc sang ngang.</p>
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-100 flex items-center gap-2">
                <AlertTriangle size={15} className="flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <FileUploader
              label="File Excel đầu vào"
              onUploadSuccess={handleUploadSuccess}
              initialFile={uploadedFile}
              onRemove={() => updateState({ uploadedFile: null, sourceColumns: [], analysisResult: null, columnConfigs: [], previewResult: null })}
            />

            {uploadedFile && (
              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setStep(1)}
                  className="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-all shadow-md hover:shadow-lg flex items-center gap-2"
                >
                  <span>Tiếp tục chọn cột →</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* ──────────────────────────────────────────────────────────── */}
        {/* BƯỚC 1: CHỌN CỘT TRÊN BẢNG                                */}
        {/* ──────────────────────────────────────────────────────────── */}
        {step === 1 && (
          <PivotColumnPicker
            uploadedFile={uploadedFile}
            sourceColumns={sourceColumns}
            loading={loading}
            error={error}
            onToggleColumn={toggleSourceColumn}
            onBack={() => setStep(0)}
            onAnalyze={handleAnalyze}
          />
        )}

        {/* ──────────────────────────────────────────────────────────── */}
        {/* BƯỚC 2: GOM NHÓM, ĐỔI TÊN & CHỌN KÝ HIỆU                */}
        {/* ──────────────────────────────────────────────────────────── */}
        {step === 2 && analysisResult && (
          <div className="space-y-4">
            <div className="flex justify-between items-center flex-wrap gap-4 bg-white p-3 rounded-2xl border border-gray-200 shadow-2xs">
              <div>
                <h2 className="text-base font-bold text-gray-800">Bước 3 — Chọn, gom nhóm & ký hiệu hiển thị</h2>
              </div>

              {/* Ký hiệu hiển thị bar placed right in the middle header space */}
              <div className="flex items-center gap-1.5 bg-gray-100 p-1 rounded-xl border border-gray-200/80 shadow-inner">
                <span className="text-xs font-semibold text-gray-600 px-2.5">Ký hiệu ô:</span>
                {[
                  { val: 'x', label: 'x' },
                  { val: '✓', label: '✓' },
                  { val: '1', label: '1' },
                  { val: 'Original', label: 'Giữ gốc' }
                ].map((opt) => (
                  <button
                    key={opt.val}
                    type="button"
                    onClick={() => updateState({ markSymbol: opt.val })}
                    className={`px-3 py-1 text-xs font-bold rounded-lg transition-all cursor-pointer ${
                      markSymbol === opt.val
                        ? 'bg-blue-600 text-white shadow-xs scale-105'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-white/80'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <button onClick={() => setStep(1)} className="px-3.5 py-1.5 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors cursor-pointer">← Quay lại</button>
                <button
                  onClick={handlePreview}
                  disabled={loading}
                  className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-all shadow-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {loading ? <><span className="animate-spin">⏳</span><span>Đang xử lý...</span></> : <span>Xem kết quả →</span>}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-100">⚠️ {error}</p>
            )}

            <div className={`grid gap-6 items-start ${analysisResult.columnsAnalysis.length > 1 ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
              {analysisResult.columnsAnalysis.map((colAna, cIdx) => {
                const isAltRow = (analysisResult.columnsAnalysis.length > 1 ? Math.floor(cIdx / 2) : cIdx) % 2 === 1;
                const isLastOdd = analysisResult.columnsAnalysis.length > 1 && analysisResult.columnsAnalysis.length % 2 === 1 && cIdx === analysisResult.columnsAnalysis.length - 1;
                return (
                  <div
                    key={cIdx}
                    className={`rounded-xl border shadow-sm overflow-hidden transition-all ${
                      isAltRow ? 'bg-[#F8FAFC] border-gray-300' : 'bg-white border-gray-200'
                    } ${isLastOdd ? 'lg:col-span-2' : ''}`}
                  >
                    <div className={`px-5 py-3 border-b flex items-center justify-between flex-wrap gap-2 ${
                      isAltRow ? 'bg-gray-100/80 border-gray-200' : 'bg-gray-50 border-gray-100'
                    }`}>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-semibold uppercase tracking-wider ${isAltRow ? 'text-gray-500' : 'text-gray-400'}`}>Cột gốc</span>
                        <span className="text-sm font-bold text-gray-800">{colAna.sourceColumn}</span>
                      </div>
                      <div className="flex items-center gap-4 ml-auto">
                        <span className={`text-xs font-medium px-3 py-1 rounded-lg border shadow-2xs ${
                          isAltRow ? 'bg-white text-gray-700 border-gray-300' : 'bg-white text-gray-600 border-gray-200'
                        }`}>
                          {colAna.uniqueValues.length} giá trị · Tổng {analysisResult.totalRows} dòng
                        </span>
                        <div className="flex items-center gap-2">
                          <button onClick={() => toggleSelectAll(cIdx, true)} className="text-xs text-blue-600 font-semibold hover:underline">Chọn tất cả</button>
                          <span className="text-gray-300">|</span>
                          <button onClick={() => toggleSelectAll(cIdx, false)} className="text-xs text-gray-500 font-semibold hover:underline">Bỏ chọn</button>
                        </div>
                      </div>
                    </div>

                    {colAna.warningMessage && (
                      <div className="px-5 py-2 bg-amber-50 border-b border-amber-200 text-amber-800 text-sm flex items-center gap-2">
                        <AlertTriangle size={15} className="flex-shrink-0 text-amber-500" />
                        <span>{colAna.warningMessage}</span>
                      </div>
                    )}

                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className={`text-[11px] uppercase tracking-wider font-semibold border-b ${
                            isAltRow ? 'bg-gray-100/60 text-gray-500 border-gray-200' : 'bg-gray-50/80 text-gray-400 border-gray-200'
                          }`}>
                            <th className="py-3 px-4 w-12 text-center">Chọn</th>
                            <th className="py-3 px-4 w-[40%]">Giá trị gốc</th>
                            <th className="py-3 px-4 w-24 text-center">Số lượng</th>
                            <th className="py-3 px-4">Tiêu đề cột đích</th>
                          </tr>
                        </thead>
                        <tbody className={`divide-y text-sm ${isAltRow ? 'divide-gray-200/60' : 'divide-gray-100'}`}>
                          {columnConfigs[cIdx].mappings.map((m, mIdx) => {
                            const count = colAna.uniqueValues[mIdx]?.count ?? 0;
                            return (
                              <tr
                                key={mIdx}
                                className={`transition-colors ${
                                  m.isSelected
                                    ? isAltRow ? 'hover:bg-blue-50/30' : 'hover:bg-blue-50/20'
                                    : isAltRow ? 'opacity-40 bg-gray-100/50' : 'opacity-40 bg-gray-50'
                                }`}
                              >
                                <td className="py-3 px-4 text-center align-middle">
                                  <input
                                    type="checkbox"
                                    checked={m.isSelected}
                                    onChange={(e) => handleMappingChange(cIdx, mIdx, 'isSelected', e.target.checked)}
                                    className="w-4 h-4 accent-blue-600 rounded cursor-pointer"
                                  />
                                </td>
                                <td className="py-3 px-4 align-middle font-semibold text-gray-800 text-sm">
                                  {m.originalValue || '(Trống)'}
                                </td>
                                <td className="py-3 px-4 align-middle text-center">
                                  <span className={`inline-block px-2.5 py-0.5 rounded text-xs font-mono font-medium border ${
                                    isAltRow ? 'bg-white text-gray-800 border-gray-300 shadow-2xs' : 'bg-gray-100 text-gray-700 border-gray-200/80'
                                  }`}>
                                    {count}
                                  </span>
                                </td>
                                <td className="py-3 px-4 align-middle">
                                  <input
                                    type="text"
                                    disabled={!m.isSelected}
                                    value={m.targetColumnName}
                                    onChange={(e) => handleMappingChange(cIdx, mIdx, 'targetColumnName', e.target.value)}
                                    placeholder="Nhập tiêu đề cột đích..."
                                    className={`w-full px-3 py-2 border rounded-xl text-sm font-medium text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-sm ${
                                      isAltRow
                                        ? 'bg-white border-gray-300 disabled:bg-gray-100 disabled:text-gray-400'
                                        : 'bg-white border-gray-200 disabled:bg-gray-100/60 disabled:text-gray-400'
                                    }`}
                                  />
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ──────────────────────────────────────────────────────────── */}
        {/* BƯỚC 3: KẾT QUẢ PREVIEW & XUẤT FILE                        */}
        {/* ──────────────────────────────────────────────────────────── */}
        {step === 3 && previewResult && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-base font-semibold text-gray-800">Bước 4 — Xem trước & Xuất file kết quả</h2>
              <div className="flex items-center gap-2">
                <button onClick={() => setStep(2)} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors cursor-pointer">← Quay lại</button>
                <button onClick={() => { resetPivotState(); }} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">🔄 Bắt đầu lại</button>
                <button
                  onClick={handleExport}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
                >
                  <Download size={15} />
                  <span>📥 Xuất Excel</span>
                </button>
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-100">⚠️ {error}</p>
            )}

            {/* Stats Compact Bar */}
            <div className="bg-gray-50 rounded-xl p-3 border border-gray-200/80 shadow-2xs flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="text-gray-500 font-medium">Tổng dòng:</span>
                  <span className="font-bold text-blue-600 text-base">{previewResult.totalRows?.toLocaleString()}</span>
                </div>
                <div className="w-px h-4 bg-gray-300 hidden sm:block" />
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="text-gray-500 font-medium">Cột xuất ra:</span>
                  <span className="font-bold text-orange-600 text-base">{previewResult.headers.length}</span>
                </div>
                <div className="w-px h-4 bg-gray-300 hidden sm:block" />
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="text-gray-500 font-medium">Cột mới tạo:</span>
                  <span className="font-bold text-green-600 text-base">{Object.keys(previewResult.columnStats).length}</span>
                </div>
              </div>

              {/* Thống kê số lượng đánh dấu từng cột mới (dạng pills gọn gàng) */}
              {Object.keys(previewResult.columnStats).length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-xs font-semibold text-gray-500 mr-1">Chi tiết từng cột:</span>
                  {Object.entries(previewResult.columnStats).map(([colName, count], idx) => (
                    <span key={idx} className="inline-flex items-center gap-1 bg-white px-2 py-0.5 rounded-md border border-gray-200/80 text-xs shadow-2xs">
                      <span className="font-medium text-gray-700 max-w-[120px] truncate" title={colName}>{colName}:</span>
                      <span className="font-bold text-blue-600 bg-blue-50/80 px-1 rounded">{count}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Preview Table */}
            <div className="rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex flex-wrap items-center justify-between gap-3">
                <h3 className="font-semibold text-gray-800 text-sm flex items-center gap-2">
                  Xem trước dữ liệu
                  <span className="font-normal text-blue-600 text-xs bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">💡 Nhấn vào tiêu đề cột bất kỳ để gom/sắp xếp dữ liệu</span>
                </h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 font-medium">Vị trí đặt cột mới:</span>
                  <select
                    value={placement}
                    onChange={(e) => handlePlacementChange(e.target.value)}
                    disabled={loading}
                    className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-blue-500 bg-white shadow-2xs"
                  >
                    <option value="Replace">Thay thế (xóa cột gốc)</option>
                    <option value="AfterSource">Giữ cột gốc (đặt kề sau)</option>
                    <option value="End">Giữ cột gốc (đặt cuối bảng)</option>
                  </select>
                  {loading && <RefreshCw size={16} className="animate-spin text-blue-500" />}
                </div>
              </div>
              <div className="overflow-x-auto max-h-[620px]">
                <table className="w-full text-left border-collapse text-sm whitespace-nowrap">
                  <thead>
                    <tr className="bg-gray-100 text-gray-600 text-xs font-semibold uppercase border-b border-gray-200 sticky top-0 z-10">
                      <th className="py-2.5 px-3 w-12 text-center bg-gray-200/90 text-gray-700 font-bold border-r border-gray-300 sticky left-0 z-20 shadow-2xs">STT</th>
                      {previewResult.headers.map((h, idx) => {
                        const isPivot = Object.prototype.hasOwnProperty.call(previewResult.columnStats, h);
                        const isSorted = sortColumn === h;
                        return (
                          <th
                            key={idx}
                            onClick={() => handleSortColumn(h)}
                            title="Nhấn để sắp xếp / đưa dữ liệu cột này lên đầu"
                            className={`py-2.5 px-4 cursor-pointer select-none transition-colors hover:bg-blue-100/80 group ${
                              isPivot ? 'bg-blue-50/40 text-blue-900 font-bold border-x border-blue-100' : ''
                            } ${isSorted ? '!bg-blue-100 text-blue-950 shadow-inner' : ''}`}
                          >
                            <div className="flex items-center justify-between gap-1.5">
                              <span>{h}</span>
                              {isSorted ? (
                                sortDirection === 'desc' ? <ArrowDown size={14} className="text-blue-600 shrink-0" /> : <ArrowUp size={14} className="text-blue-600 shrink-0" />
                              ) : (
                                <ArrowUpDown size={12} className="text-gray-400 opacity-40 group-hover:opacity-100 shrink-0 transition-opacity" />
                              )}
                            </div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {sortedPreviewRows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-gray-50/80 transition-colors">
                        <td className="py-2.5 px-3 text-center text-xs font-semibold text-gray-600 bg-gray-100/90 border-r border-gray-200 sticky left-0 z-10 select-none shadow-2xs">{rIdx + 1}</td>
                        {previewResult.headers.map((h, cIdx) => {
                          const val = row[h];
                          const isPivot = Object.prototype.hasOwnProperty.call(previewResult.columnStats, h);
                          const isMarked = val !== null && val !== undefined && val !== '';
                          return (
                            <td key={cIdx} className={`py-2.5 px-4 ${isPivot ? 'text-center border-x border-blue-100/60 bg-blue-50/10' : 'text-gray-700'}`}>
                              {isPivot && isMarked
                                ? <span className="text-gray-800 text-sm select-all">{val === 'X' ? 'x' : val}</span>
                                : <span className="text-sm">{val !== null && val !== undefined ? (val === 'X' ? 'x' : String(val)) : ''}</span>
                              }
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
    </div>
  );
}
