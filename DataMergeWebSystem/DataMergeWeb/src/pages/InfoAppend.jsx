import { useState, useCallback } from 'react';
import { Layers, ArrowRight, GripVertical, Check } from 'lucide-react';
import FileUploader from '../components/FileUploader/FileUploader';
import BaseTable from '../components/BaseTable/BaseTable';
import { leftJoin, exportInfoAppendResult, downloadBlob } from '../services/excelService';
import { useAppContext } from '../contexts/AppContext';

export default function InfoAppend() {
  const { infoState, setInfoState, resetInfoState } = useAppContext();
  const { step, masterFile, auxFiles, keyColumns, mappings, result } = infoState;

  const [dragSource, setDragSource] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const setStep = (v) => setInfoState(p => ({ ...p, step: typeof v === 'function' ? v(p.step) : v }));
  const setMasterFile = (v) => {
    setInfoState(p => ({ ...p, masterFile: typeof v === 'function' ? v(p.masterFile) : v }));
    setKeyColumns([]);
    setMappings([]);
    setResult(null);
  };
  const setAuxFiles = (v) => {
    setInfoState(p => ({ ...p, auxFiles: typeof v === 'function' ? v(p.auxFiles) : v }));
    setKeyColumns([]);
    setMappings([]);
    setResult(null);
  };
  const setKeyColumns = (v) => setInfoState(p => ({ ...p, keyColumns: typeof v === 'function' ? v(p.keyColumns) : v }));
  const setMappings = (v) => setInfoState(p => ({ ...p, mappings: typeof v === 'function' ? v(p.mappings) : v }));
  const setResult = (v) => setInfoState(p => ({ ...p, result: typeof v === 'function' ? v(p.result) : v }));

  const handleAuxUpload = (idx, info) => {
    setAuxFiles(prev => { const a = [...prev]; a[idx] = info; return a; });
  };

  const toggleKeyCol = (col) => {
    setKeyColumns(prev => prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]);
  };

  // Drag: source là cột từ file phụ
  const handleDragStart = (col, auxFile) => setDragSource({ col, auxFile });

  // Drop: thả lên cột master để tạo mapping
  const handleDrop = (masterCol) => {
    if (!dragSource) return;
    const exists = mappings.find(m => m.masterColumn === masterCol && m.auxFileId === dragSource.auxFile.fileId);
    if (!exists) {
      setMappings(prev => [...prev, {
        masterColumn: masterCol,
        auxFileId: dragSource.auxFile.fileId,
        auxColumn: dragSource.col,
        outputColumnName: dragSource.col,
      }]);
    }
    setDragSource(null);
  };

  const removeMapping = (idx) => setMappings(prev => prev.filter((_, i) => i !== idx));

  const handleJoin = async () => {
    if (!masterFile) { setError('Cần chọn File Gốc.'); return; }
    const validAux = auxFiles.filter(f => f !== null);
    if (validAux.length === 0) { setError('Cần ít nhất 1 File Phụ.'); return; }
    if (keyColumns.length === 0) { setError('Cần chọn ít nhất 1 cột khóa.'); return; }
    setError('');
    setLoading(true);
    try {
      const res = await leftJoin(
        masterFile.fileId,
        validAux.map(f => f.fileId),
        mappings,
        keyColumns
      );
      setResult(res.data);
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.message || 'Xử lý thất bại.');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    const res = await exportInfoAppendResult(result.rows);
    downloadBlob(res, 'KetQua_BoSungThongTin.xlsx');
  };

  const allHeaders = result?.headers?.map(h => ({ Header: h, accessor: h })) ?? [];

  return (
    <div className="max-w-[1400px] mx-auto space-y-6">
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
        <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center"><Layers size={24} /></div>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Bổ sung thông tin</h1>
          <p className="text-gray-500">Ghép nối cột từ file phụ vào file gốc (Left Join) theo khóa chung.</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        {/* Step 0: Upload */}
        {step === 0 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-800">Upload Files</h2>
            <FileUploader label="📌 File Gốc (Master File)" onUploadSuccess={setMasterFile} initialFile={masterFile} onRemove={() => setMasterFile(null)} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FileUploader label="File Phụ 1 (Auxiliary)" onUploadSuccess={(info) => handleAuxUpload(0, info)} initialFile={auxFiles[0]} onRemove={() => handleAuxUpload(0, null)} />
              <FileUploader label="File Phụ 2 (tuỳ chọn)" onUploadSuccess={(info) => handleAuxUpload(1, info)} initialFile={auxFiles[1]} onRemove={() => handleAuxUpload(1, null)} />
            </div>
            <div className="flex justify-end">
              <button onClick={() => setStep(1)} disabled={!masterFile} className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50">
                Tiếp theo →
              </button>
            </div>
          </div>
        )}

        {/* Step 1: Cấu hình khóa */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800">Chọn cột khóa chung</h2>
            <p className="text-sm text-gray-500">Chọn cột xuất hiện ở cả file Gốc và file Phụ để làm khóa join.</p>
            <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
              {(masterFile?.headers ?? []).map(h => (
                <label key={h} className={`flex items-center space-x-2 p-2.5 rounded-lg border cursor-pointer text-sm ${
                  keyColumns.includes(h) ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-gray-200 hover:border-indigo-300'
                }`}>
                  <input type="checkbox" checked={keyColumns.includes(h)} onChange={() => toggleKeyCol(h)} className="accent-indigo-600" />
                  <span className="truncate font-medium" title={h}>{h}</span>
                </label>
              ))}
            </div>
            <div className="flex justify-between mt-4">
              <button onClick={() => setStep(0)} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50">← Quay lại</button>
              <button onClick={() => setStep(2)} disabled={keyColumns.length === 0} className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 disabled:opacity-50">Tiếp theo →</button>
            </div>
          </div>
        )}

        {/* Step 2: Drag & Drop Mapping */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800">Ghép cột (Drag & Drop)</h2>
            <p className="text-sm text-gray-500">Kéo cột từ <strong>File Phụ</strong> và thả lên cột <strong>File Gốc</strong> muốn đắp thêm dữ liệu.</p>

            <div className="grid grid-cols-2 gap-6">
              {/* Cột File Gốc (drop targets) */}
              <div>
                <div className="font-semibold text-gray-700 mb-2 text-sm">📌 File Gốc: <span className="text-indigo-600">{masterFile?.fileName}</span></div>
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {(masterFile?.headers ?? []).map(col => (
                    <div key={col}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={() => handleDrop(col)}
                      className="flex items-center justify-between px-3 py-2 border border-dashed border-gray-300 rounded-lg hover:border-indigo-400 hover:bg-indigo-50/50 transition-colors text-sm cursor-pointer"
                    >
                      <span className="font-medium text-gray-700">{col}</span>
                      {mappings.filter(m => m.masterColumn === col).map((m, i) => (
                        <span key={i} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full ml-2">← {m.auxColumn}</span>
                      ))}
                    </div>
                  ))}
                </div>
              </div>

              {/* Cột File Phụ (drag sources) */}
              <div>
                {auxFiles.filter(Boolean).map((auxFile, fi) => (
                  <div key={fi} className="mb-4">
                    <div className="font-semibold text-gray-700 mb-2 text-sm">📎 File Phụ {fi + 1}: <span className="text-gray-500">{auxFile?.fileName}</span></div>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {(auxFile?.headers ?? []).map(col => (
                        <div key={col} draggable
                          onDragStart={() => handleDragStart(col, auxFile)}
                          className="flex items-center space-x-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg cursor-grab active:cursor-grabbing hover:bg-indigo-50 hover:border-indigo-300 transition-colors text-sm"
                        >
                          <GripVertical size={14} className="text-gray-400 flex-shrink-0" />
                          <span>{col}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Mapping list */}
            {mappings.length > 0 && (
              <div className="mt-4">
                <div className="text-sm font-semibold text-gray-700 mb-2">Danh sách mapping đã tạo:</div>
                <div className="space-y-1">
                  {mappings.map((m, i) => (
                    <div key={i} className="flex items-center justify-between px-3 py-2 bg-indigo-50 rounded-lg text-sm">
                      <span><strong>{m.masterColumn}</strong> ← {m.auxColumn}</span>
                      <button onClick={() => removeMapping(i)} className="text-red-400 hover:text-red-600 ml-2">✕</button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex justify-between mt-4">
              <button onClick={() => setStep(1)} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50">← Quay lại</button>
              <button onClick={handleJoin} disabled={loading} className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center space-x-2">
                {loading ? <><span className="animate-spin">⏳</span><span>Đang xử lý...</span></> : <span>✅ Thực hiện Ghép nối</span>}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Kết quả */}
        {step === 3 && result && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-indigo-50 rounded-xl p-4 text-center border border-indigo-100">
                <div className="text-3xl font-bold text-indigo-600">{result.totalInput?.toLocaleString()}</div>
                <div className="text-sm text-gray-500 mt-1">Dòng file Gốc</div>
              </div>
              <div className="bg-green-50 rounded-xl p-4 text-center border border-green-100">
                <div className="text-3xl font-bold text-green-600">{result.totalOutput?.toLocaleString()}</div>
                <div className="text-sm text-gray-500 mt-1">Dòng kết quả</div>
              </div>
            </div>
            <BaseTable columns={allHeaders} data={result.rows ?? []} title="Kết quả Bổ sung Thông tin" enableExport={false} />
            <div className="flex justify-between mt-2">
              <button onClick={() => resetInfoState()} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50">🔄 Làm lại</button>
              <button onClick={handleExport} className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700">📥 Xuất Excel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
