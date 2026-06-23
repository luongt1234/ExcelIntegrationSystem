import { useState } from 'react';
import { Users, ArrowRight, Check } from 'lucide-react';
import FileUploader from '../components/FileUploader/FileUploader';
import BaseTable from '../components/BaseTable/BaseTable';
import FileStructurePreview from '../components/FileStructurePreview';
import { mergePeople, getFileData, exportPeopleResult, downloadBlob } from '../services/excelService';
import { getStandardizedColumnName } from '../utils/hrDictionary';

const MODES = [
  { id: 1, label: 'Gộp & Loại trùng (Union/Dedup)', desc: 'Gộp nhiều file, tự động loại bỏ dòng trùng theo khóa.' },
  { id: 2, label: 'Nối dài dữ liệu (Append)', desc: 'Chỉ nối các dòng từ file phụ vào file gốc, không loại trùng.' },
];

const STEPS = ['Chọn Chế độ', 'Upload Files', 'Xác nhận & Chuẩn hóa', 'Cấu hình Khóa', 'Kết quả'];

export default function PeopleMerge() {
  const [step, setStep] = useState(0);
  const [mode, setMode] = useState(1);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [verifiedFiles, setVerifiedFiles] = useState([]);
  const [fileMappings, setFileMappings] = useState({});
  const [globalSuggestedMappings, setGlobalSuggestedMappings] = useState({});
  const [keyColumns, setKeyColumns] = useState([]);
  const [availableHeaders, setAvailableHeaders] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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

  const handleFileUploaded = (info) => {
    setUploadedFiles(prev => {
      const updated = [...prev.filter(f => f.fileId !== info.fileId), info];
      
      const allHeadersMap = {};
      updated.forEach(file => {
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
      updated.forEach(file => {
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
  };

  const toggleKeyColumn = (col) => {
    setKeyColumns(prev => prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]);
  };

  const handleMerge = async () => {
    if (uploadedFiles.length === 0) { setError('Cần ít nhất 1 file.'); return; }
    setError('');
    setLoading(true);
    try {
      const keyColumnsByFile = {};
      const selectedSheetByFile = {};
      uploadedFiles.forEach(f => {
        keyColumnsByFile[f.fileId] = keyColumns;
        selectedSheetByFile[f.fileId] = f.selectedSheet;
      });
      const config = {
        mergeMode: mode,
        keyColumnsByFile,
        columnMappingsByFile: fileMappings,
        selectedSheetByFile
      };
      const res = await mergePeople(uploadedFiles.map(f => f.fileId), config);
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
      setVerifiedFiles(prev => [...prev, fileId]);
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
      setUploadedFiles(prev => prev.map(f => f.fileId === fileId ? { ...res.data, fileId: res.data.filePath, fileName: f.fileName } : f));
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

  return (
    <div className="max-w-5xl mx-auto space-y-6">


      {/* Step Progress */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 relative">
        <div className="flex justify-between relative z-10">
          {STEPS.map((s, i) => (
            <div 
              key={i} 
              onClick={() => i < step ? setStep(i) : null}
              className={`flex flex-col items-center flex-1 transition-all ${
                i <= step ? 'text-blue-600' : 'text-gray-400'
              } ${i < step ? 'cursor-pointer hover:opacity-80' : ''}`}
              title={i < step ? 'Click để quay lại bước này' : ''}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm mb-2 transition-colors ${
                i < step ? 'bg-blue-600 text-white shadow-md' : 
                i === step ? 'bg-blue-100 text-blue-600 ring-4 ring-blue-50' : 
                'bg-gray-100 text-gray-400'
              }`}>
                {i < step ? '✓' : i + 1}
              </div>
              <span className="text-xs font-medium uppercase tracking-wide">{s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        {/* Step 0: Chọn chế độ */}
        {step === 0 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Chọn chế độ xử lý</h2>
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
            <div className="flex justify-end mt-4">
              <button onClick={() => setStep(1)} className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors">
                Tiếp theo →
              </button>
            </div>
          </div>
        )}

        {/* Step 1: Upload files */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Upload file Excel {mode === 3 ? '(1 file)' : '(nhiều file)'}</h2>
            {(mode === 3 ? [0] : [0, 1, 2]).map(idx => (
              <FileUploader key={idx} label={`File ${idx + 1}`} onUploadSuccess={handleFileUploaded} />
            ))}
            <div className="flex justify-between mt-4">
              <button onClick={() => setStep(0)} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">← Quay lại</button>
              <button onClick={() => setStep(2)} disabled={uploadedFiles.length === 0} className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Tiếp theo →</button>
            </div>
          </div>
        )}

        {/* Step 2: Xác nhận cấu trúc từng file */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-1">Bước 2: Kiểm tra & Đồng bộ Cột</h2>
            <div className={`grid grid-cols-1 ${uploadedFiles.length > 1 ? 'lg:grid-cols-2' : ''} gap-4`}>
              {uploadedFiles.map((file) => (
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
            <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100">
              <button onClick={() => setStep(1)} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">← Quay lại upload</button>
              <div className="flex items-center space-x-4">
                {verifiedFiles.length === uploadedFiles.length ? (
                  <span className="text-sm text-green-600 font-medium">✅ Tất cả {uploadedFiles.length} file đã xác nhận</span>
                ) : (
                  <span className="text-sm text-orange-500 font-medium">⚠️ Đang chờ xác nhận ({verifiedFiles.length}/{uploadedFiles.length})</span>
                )}
                <button 
                  onClick={() => setStep(3)} 
                  disabled={verifiedFiles.length !== uploadedFiles.length || uploadedFiles.length === 0} 
                  className="px-6 py-2.5 bg-orange-600 text-white rounded-xl font-medium hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Tiếp theo: Chọn khóa →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Cấu hình khóa */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Bước 3: Chọn khóa quét trùng</h2>
              <p className="text-sm text-gray-500 mb-4">Các file đã xác nhận cấu trúc. Chọn khóa kết hợp để phát hiện bản ghi trùng.</p>
            </div>

            {/* Danh sách file */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
                <h3 className="font-semibold text-gray-800">Danh sách file đã nạp:</h3>
              </div>
              <div className="p-5 space-y-3">
                {verifiedFiles.map((fileId, idx) => {
                  const fileObj = uploadedFiles.find(f => f.fileId === fileId);
                  const keptCols = Object.keys(fileMappings[fileId] || {}).length;
                  if (!fileObj) return null;
                  return (
                    <div key={idx} className="flex flex-wrap items-center text-blue-800 font-medium bg-blue-50/50 px-4 py-2.5 rounded-lg border border-blue-100">
                      <span className="mr-2">📄</span>
                      <span>{fileObj.fileName}</span>
                      <span className="mx-3 text-blue-300">—</span>
                      <span className="text-blue-600 font-normal">{keptCols} cột giữ lại (sau đồng bộ)</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Cấu hình khóa */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
                <h3 className="font-semibold text-gray-800">Chọn tiêu chí kết hợp để quét trùng <span className="text-gray-500 font-normal text-sm ml-1">(nên chọn ít nhất 2 khóa):</span></h3>
              </div>
              <div className="p-5">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {availableHeaders.map(h => (
                    <label key={h} className={`flex items-center space-x-3 p-3 rounded-xl border cursor-pointer transition-all ${
                      keyColumns.includes(h) ? 'border-orange-500 bg-orange-50 text-orange-800 shadow-sm' : 'border-gray-200 hover:border-orange-300 hover:bg-orange-50/30'
                    }`}>
                      <input type="checkbox" checked={keyColumns.includes(h)} onChange={() => toggleKeyColumn(h)} className="w-4 h-4 accent-orange-600 rounded cursor-pointer" />
                      <span className="font-medium truncate" title={h}>{h}</span>
                    </label>
                  ))}
                </div>
                {error && <p className="text-sm text-red-600 mt-4 bg-red-50 px-3 py-2 rounded-lg border border-red-100 inline-block">⚠️ {error}</p>}
              </div>
            </div>

            <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100">
              <button onClick={() => setStep(2)} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">← Quay lại kiểm tra</button>
              <button onClick={handleMerge} disabled={loading} className="px-8 py-3 bg-orange-600 text-white rounded-xl font-bold hover:bg-orange-700 transition-colors disabled:opacity-50 flex items-center space-x-2 shadow-sm">
                {loading ? <><span className="animate-spin">⏳</span><span>Đang xử lý...</span></> : <span>▶ Tiến hành Quét & Khử trùng ➔</span>}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Kết quả */}
        {step === 4 && result && (
          <div className="space-y-4">
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
            <div className="flex justify-between mt-2">
              <div className="flex space-x-3">
                <button onClick={() => setStep(3)} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">← Quay lại Chọn Khóa</button>
                <button onClick={() => { setStep(0); setResult(null); setUploadedFiles([]); setVerifiedFiles([]); setKeyColumns([]); setFileMappings({}); setGlobalSuggestedMappings({}); }} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">🔄 Bắt đầu lại</button>
              </div>
              <button onClick={handleExport} className="px-6 py-2.5 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors">📥 Xuất Excel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
