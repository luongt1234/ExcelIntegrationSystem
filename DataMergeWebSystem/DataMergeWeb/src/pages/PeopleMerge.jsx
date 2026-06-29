import React, { useState, useEffect } from 'react';
import { Users, ArrowRight, Check } from 'lucide-react';
import FileUploader from '../components/FileUploader/FileUploader';
import BaseTable from '../components/BaseTable/BaseTable';
import FileStructurePreview from '../components/FileStructurePreview';
import { mergePeople, getFileData, exportPeopleResult, downloadBlob } from '../services/excelService';
import { getStandardizedColumnName } from '../utils/hrDictionary';
import { useAppContext } from '../contexts/AppContext';

const MODES = [
  { id: 1, label: 'Gộp & Loại trùng (Union/Dedup)', desc: 'Gộp nhiều file, tự động loại bỏ dòng trùng theo khóa.' },
];

const STEPS = ['Chọn Chế độ', 'Upload Files', 'Chọn & Ghép Cột', 'Cấu hình Khóa', 'Kết quả'];

export default function PeopleMerge() {
  const { peopleState, setPeopleState, resetPeopleState, setHeaderCenterContent } = useAppContext();
  const { step, uploadedFiles, verifiedFiles, fileMappings, globalSuggestedMappings, keyColumns, availableHeaders, result, previewStates } = peopleState;
  const validFiles = uploadedFiles.filter(Boolean);

  const [mode, setMode] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const setStep = React.useCallback((v) => setPeopleState(p => ({ ...p, step: typeof v === 'function' ? v(p.step) : v })), [setPeopleState]);
  const setUploadedFiles = (v) => setPeopleState(p => ({ ...p, uploadedFiles: typeof v === 'function' ? v(p.uploadedFiles) : v }));
  const setVerifiedFiles = (v) => setPeopleState(p => ({ ...p, verifiedFiles: typeof v === 'function' ? v(p.verifiedFiles) : v }));
  const setFileMappings = (v) => setPeopleState(p => ({ ...p, fileMappings: typeof v === 'function' ? v(p.fileMappings) : v }));
  const setGlobalSuggestedMappings = (v) => setPeopleState(p => ({ ...p, globalSuggestedMappings: typeof v === 'function' ? v(p.globalSuggestedMappings) : v }));
  const setKeyColumns = (v) => setPeopleState(p => ({ ...p, keyColumns: typeof v === 'function' ? v(p.keyColumns) : v }));
  const setAvailableHeaders = (v) => setPeopleState(p => ({ ...p, availableHeaders: typeof v === 'function' ? v(p.availableHeaders) : v }));
  const setResult = (v) => setPeopleState(p => ({ ...p, result: typeof v === 'function' ? v(p.result) : v }));
  const setPreviewStates = (v) => setPeopleState(p => ({ ...p, previewStates: typeof v === 'function' ? v(p.previewStates) : v }));

  const handleGoToStep3 = () => setStep(3);

  const normalizeText = (text) => {
    if (!text) return '';
    let str = text.toLowerCase().trim();
    str = str.replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, "a");
    str = str.replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, "e");
    str = str.replace(/ì|í|ị|ỉ|ĩ/g, "i");
    str = str.replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, "o");
    str = str.replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, "u");
    str = str.replace(/ỳ|ý|ỵ|ỷ|ỹ/g, "y");
    str = str.replace(/đ/g, "d");
    str = str.replace(/\u0300|\u0301|\u0303|\u0309|\u0323/g, ""); 
    str = str.replace(/\u02C6|\u0306|\u031B/g, ""); 
    return str.replace(/[^a-z0-9]/g, '');
  };

  const handleFileUploaded = (idx, info) => {
    setUploadedFiles(prev => {
      const updated = [...prev];
      updated[idx] = info;
      
      const validFiles = updated.filter(Boolean);
      
      const allHeadersMap = {};
      validFiles.forEach(file => {
        if (file.headers) {
          file.headers.forEach(h => {
            const standardName = getStandardizedColumnName(h);
            const norm = normalizeText(standardName);
            if (!allHeadersMap[norm]) {
              allHeadersMap[norm] = standardName;
            }
          });
        }
      });
      
      const suggested = {};
      validFiles.forEach(file => {
        if (file.headers) {
          file.headers.forEach(h => {
            const standardName = getStandardizedColumnName(h);
            const norm = normalizeText(standardName);
            suggested[h] = allHeadersMap[norm] || standardName;
          });
        }
      });
      
      setGlobalSuggestedMappings(suggested);
      return updated;
    });
    
    // Xóa các bước sau khi có file mới tải đè lên
    setVerifiedFiles([]);
    setFileMappings({});
    setKeyColumns([]);
    setResult(null);
    setPreviewStates({});
  };

  const toggleKeyColumn = (col) => {
    setKeyColumns(prev => prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]);
  };

  const handleMerge = async () => {
    const validFiles = uploadedFiles.filter(Boolean);
    if (validFiles.length === 0) { setError('Cần ít nhất 1 file.'); return; }
    setError('');
    setLoading(true);
    try {
      const keyColumnsByFile = {};
      const selectedSheetByFile = {};
      validFiles.forEach(f => {
        keyColumnsByFile[f.fileId] = keyColumns;
        selectedSheetByFile[f.fileId] = f.selectedSheet;
      });
      const config = {
        mergeMode: mode,
        keyColumnsByFile,
        columnMappingsByFile: fileMappings,
        selectedSheetByFile
      };
      const res = await mergePeople(validFiles.map(f => f.fileId), config);
      setResult(res.data);
      setStep(4);
    } catch (err) {
      setError(err.response?.data?.message || 'Xử lý thất bại.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyToggle = (fileId, mappings) => {
    if (mappings) {
      setVerifiedFiles(prev => [...new Set([...prev, fileId])]);
      setFileMappings(prev => {
        const next = { ...prev, [fileId]: mappings };
        // Cập nhật availableHeaders dựa trên tên cột mới sau khi map
        const allHeaders = new Set();
        Object.values(next).forEach(fileMap => {
          Object.values(fileMap).forEach(newName => allHeaders.add(newName));
        });
        setAvailableHeaders(Array.from(allHeaders));
        return next;
      });
    } else {
      setVerifiedFiles(prev => prev.filter(id => id !== fileId));
      setFileMappings(prev => {
        const next = { ...prev };
        delete next[fileId];
        // Cập nhật lại availableHeaders
        const allHeaders = new Set();
        Object.values(next).forEach(fileMap => {
          Object.values(fileMap).forEach(newName => allHeaders.add(newName));
        });
        setAvailableHeaders(Array.from(allHeaders));
        return next;
      });
    }
  };

  const handleSheetChange = async (fileId, newSheetName) => {
    try {
      const { getFileStructure } = await import('../services/excelService');
      const res = await getFileStructure(fileId, newSheetName);
      setUploadedFiles(prev => prev.map(f => f?.fileId === fileId ? { ...res.data, fileId: res.data.filePath, fileName: f.fileName } : f));
      // Xóa verified status khi đổi sheet
      setVerifiedFiles(prev => prev.filter(id => id !== fileId));
    } catch (err) {
      console.error('Lỗi khi đổi sheet:', err);
    }
  };

  const handleExport = async () => {
    if (!result?.rows) return;
    const res = await exportPeopleResult(result.rows);
    downloadBlob(res, 'KetQua_GopHoSo.xlsx');
  };

  const columns = result?.headers?.map(h => ({ Header: h, accessor: h })) ?? [];

  // Tính toán các khóa hợp lệ (xuất hiện ở >= 2 file nếu có nhiều file)
  const headerCounts = {};
  verifiedFiles.forEach(fileId => {
    const mapping = fileMappings[fileId] || {};
    const stdCols = new Set(Object.values(mapping));
    stdCols.forEach(col => {
      headerCounts[col] = (headerCounts[col] || 0) + 1;
    });
  });
  
  // Danh sách các từ khóa KHÔNG nên dùng làm khóa quét trùng
  const EXCLUDED_KEYWORDS = ['vị trí', 'ứng tuyển', 'chức vụ', 'phòng ban', 'phòng', 'ban', 'đơn vị', 'câu hỏi', 'gk1', 'gk2', 'gk3', 'gk4', 'gk5', 'điểm', 'thời gian', 'ghi chú', 'kết quả', 'stt', 'chuẩn bị', 'điều kiện', 'col', 'đánh giá', 'nhận xét'];

  const candidateKeys = (verifiedFiles.length > 1 
    ? availableHeaders.filter(col => headerCounts[col] > 1)
    : availableHeaders).filter(col => {
      const lower = col.toLowerCase();
      // Loại bỏ các cột chứa từ khóa không ổn định
      if (EXCLUDED_KEYWORDS.some(kw => lower.includes(kw))) return false;
      return true;
    });

  useEffect(() => {
    setHeaderCenterContent(
      <div className="flex justify-between items-center relative w-full max-w-[650px] h-8">
        {/* Đường line background */}
        <div className="absolute top-1/2 -translate-y-1/2 left-[10%] right-[10%] h-[2px] bg-gray-100 z-0" />
        {/* Đường line progress */}
        <div 
          className="absolute top-1/2 -translate-y-1/2 left-[10%] h-[2px] bg-blue-500 z-0 transition-all duration-500" 
          style={{ width: `${step * 20}%` }} 
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
            {/* Chữ được đưa xuống absolute để không đẩy vòng tròn lên lệch khỏi tâm */}
            <span className={`absolute top-[120%] left-1/2 -translate-x-1/2 w-[140%] text-[9px] uppercase tracking-wider text-center leading-tight transition-all duration-300 ${i === step ? 'font-bold' : 'font-medium'}`}>{s}</span>
          </div>
        ))}
      </div>
    );
    return () => setHeaderCenterContent(null);
  }, [step, setStep, setHeaderCenterContent]);

  return (
    <div className="max-w-[1400px] mx-auto space-y-6">

      {/* Step Content */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        {/* Step 0: Chọn chế độ */}
        {step === 0 && (
          <div className="space-y-4">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-base font-semibold text-gray-800">Chọn chế độ xử lý</h2>
              <button onClick={() => setStep(1)} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center space-x-2 shadow-sm">
                <span>Tiếp theo →</span>
              </button>
            </div>
            {MODES.map(m => (
              <label key={m.id} className={`flex items-start space-x-3 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                mode === m.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
              }`}>
                <input type="radio" name="mode" value={m.id} checked={mode === m.id} onChange={() => setMode(m.id)} className="mt-1" />
                <div>
                  <p className="font-semibold text-gray-800">{m.label}</p>
                  <p className="text-sm text-gray-500">{m.desc}</p>
                </div>
              </label>
            ))}
          </div>
        )}

        {/* Step 1: Upload files */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-base font-semibold text-gray-800">Upload file Excel {mode === 3 ? '(1 file)' : '(nhiều file)'}</h2>
              <div className="flex items-center gap-2">
                <button onClick={() => setStep(0)} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">← Quay lại</button>
                <button onClick={() => setStep(2)} disabled={uploadedFiles.filter(Boolean).length === 0} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm">Tiếp theo →</button>
              </div>
            </div>
            {(mode === 3 ? [0] : [0, 1, 2]).map(idx => (
              <FileUploader 
                key={idx} 
                label={`File ${idx + 1}`} 
                onUploadSuccess={(info) => handleFileUploaded(idx, info)} 
                initialFile={uploadedFiles[idx]} 
                onRemove={() => handleFileUploaded(idx, null)}
              />
            ))}
          </div>
        )}

        {/* Step 2: Xác nhận cấu trúc từng file */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-base font-semibold text-gray-800">Chọn cột & Ghép cột</h2>
              <div className="flex items-center gap-3">
                {verifiedFiles.length === validFiles.length ? (
                  <span className="text-sm text-green-600 font-medium">✅ Tất cả {validFiles.length} file đã xác nhận</span>
                ) : (
                  <span className="text-sm text-orange-500 font-medium">⚠️ Đang chờ xác nhận ({verifiedFiles.length}/{validFiles.length})</span>
                )}
                <button onClick={() => setStep(1)} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">← Quay lại</button>
                <button 
                  onClick={() => setStep(3)} 
                  disabled={verifiedFiles.length !== validFiles.length || validFiles.length === 0} 
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                >
                  Tiếp theo →
                </button>
              </div>
            </div>
            <div className={`grid grid-cols-1 ${uploadedFiles.filter(Boolean).length > 1 ? 'lg:grid-cols-2' : ''} gap-4`}>
              {uploadedFiles.filter(Boolean).map((file) => (
                <FileStructurePreview 
                  key={file.fileId} 
                  file={file} 
                  isVerified={verifiedFiles.includes(file.fileId)}
                  onVerify={(mappings) => handleVerifyToggle(file.fileId, mappings)}
                  onSheetChange={(newSheet) => handleSheetChange(file.fileId, newSheet)}
                  suggestedMappings={globalSuggestedMappings}
                />
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Cấu hình khóa */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-base font-semibold text-gray-800 mb-1">Chọn khóa quét trùng</h2>
                <p className="text-sm text-gray-500">Các file đã xác nhận cấu trúc. Chọn khóa kết hợp để phát hiện bản ghi trùng.</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setStep(2)} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">← Quay lại</button>
                <button onClick={handleMerge} disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center gap-2">
                  {loading ? <><span className="animate-spin">⏳</span><span>Đang xử lý...</span></> : <span>Tiếp theo →</span>}
                </button>
              </div>
            </div>

            {/* Cấu hình khóa */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
                <h3 className="font-semibold text-gray-800">Chọn tiêu chí kết hợp để quét trùng <span className="text-gray-500 font-normal text-sm ml-1">(nên chọn ít nhất 2 khóa):</span></h3>
              </div>
              <div className="p-5">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {candidateKeys.length > 0 ? (
                    candidateKeys.map(h => (
                      <label key={h} className={`flex items-center space-x-3 p-3 rounded-xl border cursor-pointer transition-all ${
                        keyColumns.includes(h) ? 'border-orange-500 bg-orange-50 text-orange-800 shadow-sm' : 'border-gray-200 hover:border-orange-300 hover:bg-orange-50/30'
                      }`}>
                        <input type="checkbox" checked={keyColumns.includes(h)} onChange={() => toggleKeyColumn(h)} className="w-4 h-4 accent-orange-600 rounded cursor-pointer" />
                        <span className="font-medium truncate" title={h}>{h}</span>
                      </label>
                    ))
                  ) : (
                    <p className="col-span-full text-gray-500 italic py-4">Không có cột chung nào giữa các file để làm khóa quét trùng.</p>
                  )}
                </div>
                {error && <p className="text-sm text-red-600 mt-4 bg-red-50 px-3 py-2 rounded-lg border border-red-100 inline-block">⚠️ {error}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Kết quả */}
        {step === 4 && result && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-base font-semibold text-gray-800">Kết quả Gộp Hồ Sơ</h2>
              <div className="flex items-center gap-2">
                <button onClick={() => setStep(3)} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">← Quay lại</button>
                <button onClick={() => { resetPeopleState(); setMode(1); }} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">🔄 Bắt đầu lại</button>
                <button onClick={handleExport} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors shadow-sm">📥 Xuất Excel</button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-4">
              {[
                { label: 'Tổng dòng đầu vào', value: result.totalInput, color: 'text-blue-600' },
                { label: 'Dòng trùng đã loại', value: result.totalDuplicate, color: 'text-orange-500' },
                { label: 'Kết quả cuối cùng', value: result.totalOutput, color: 'text-green-600' },
              ].map((stat, i) => (
                <div key={i} className="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
                  <div className={`text-3xl font-bold ${stat.color}`}>{stat.value?.toLocaleString()}</div>
                  <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
            <BaseTable 
              columns={(() => {
                const apiHeaders = result.headers || [];
                const allRowKeys = new Set();
                if (result.rows) {
                  result.rows.forEach(r => Object.keys(r).forEach(k => allRowKeys.add(k)));
                }
                const rowKeys = Array.from(allRowKeys);
                
                return apiHeaders.map(h => {
                  const matchingKey = rowKeys.find(k => k.toLowerCase() === h.toLowerCase()) || h;
                  return { Header: h, accessor: matchingKey };
                });
              })()} 
              data={result.rows ?? []} 
              title="Kết quả Gộp Hồ Sơ" 
              enableExport={false} 
            />
          </div>
        )}
      </div>
    </div>
  );
}
