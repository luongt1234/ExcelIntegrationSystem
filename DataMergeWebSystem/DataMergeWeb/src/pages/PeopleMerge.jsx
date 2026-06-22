import { useState } from 'react';
import { Users, ArrowRight, Check } from 'lucide-react';
import FileUploader from '../components/FileUploader/FileUploader';
import BaseTable from '../components/BaseTable/BaseTable';
import { mergePeople, getFileData, exportPeopleResult, downloadBlob } from '../services/excelService';

const MODES = [
  { id: 1, label: 'Gộp & Loại trùng (Union/Dedup)', desc: 'Gộp nhiều file, tự động loại bỏ dòng trùng theo khóa.' },
  { id: 3, label: 'Dọn dẹp 1 file (Clean Only)', desc: 'Chuẩn hóa và sắp xếp lại dữ liệu của một file duy nhất.' },
];

const STEPS = ['Chọn Chế độ', 'Upload Files', 'Cấu hình Khóa', 'Kết quả'];

export default function PeopleMerge() {
  const [step, setStep] = useState(0);
  const [mode, setMode] = useState(1);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [keyColumns, setKeyColumns] = useState([]);
  const [availableHeaders, setAvailableHeaders] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileUploaded = (info) => {
    setUploadedFiles(prev => {
      const updated = [...prev.filter(f => f.fileId !== info.fileId), info];
      // Thu thập tất cả headers từ tất cả các file
      const allHeaders = [...new Set(updated.flatMap(f => f.headers || []))];
      setAvailableHeaders(allHeaders);
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
      const keyColumnsByFile = uploadedFiles.map(() => keyColumns);
      const res = await mergePeople(uploadedFiles.map(f => f.fileId), keyColumnsByFile, mode);
      setResult(res.data);
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.message || 'Xử lý thất bại.');
    } finally {
      setLoading(false);
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
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
        <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center">
          <Users size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Dọn dẹp & Gộp Hồ Sơ</h1>
          <p className="text-gray-500">Tự động nhận diện, gộp và loại trùng dữ liệu từ nhiều file Excel.</p>
        </div>
      </div>

      {/* Step Progress */}
      <div className="flex items-center justify-between bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center">
            <div className={`flex items-center justify-center w-8 h-8 rounded-full font-semibold text-sm transition-colors ${
              i < step ? 'bg-green-500 text-white' : i === step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              {i < step ? <Check size={14} /> : i + 1}
            </div>
            <span className={`ml-2 text-sm font-medium ${i === step ? 'text-blue-600' : 'text-gray-500'}`}>{s}</span>
            {i < STEPS.length - 1 && <ArrowRight size={16} className="mx-4 text-gray-300" />}
          </div>
        ))}
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

        {/* Step 2: Cấu hình khóa */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-1">Chọn cột khóa gộp</h2>
            <p className="text-sm text-gray-500 mb-4">Chọn các cột sẽ được dùng làm khóa nhận diện trùng lặp.</p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {availableHeaders.map(h => (
                <label key={h} className={`flex items-center space-x-2 p-3 rounded-lg border cursor-pointer transition-all text-sm ${
                  keyColumns.includes(h) ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-blue-300'
                }`}>
                  <input type="checkbox" checked={keyColumns.includes(h)} onChange={() => toggleKeyColumn(h)} className="accent-blue-600" />
                  <span className="font-medium truncate" title={h}>{h}</span>
                </label>
              ))}
            </div>
            {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
            <div className="flex justify-between mt-4">
              <button onClick={() => setStep(1)} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">← Quay lại</button>
              <button onClick={handleMerge} disabled={loading} className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2">
                {loading ? <><span className="animate-spin">⏳</span><span>Đang xử lý...</span></> : <span>✅ Thực hiện Gộp</span>}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Kết quả */}
        {step === 3 && result && (
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
            <BaseTable columns={columns} data={result.rows ?? []} title="Kết quả Gộp Hồ Sơ" enableExport={false} />
            <div className="flex justify-between mt-2">
              <button onClick={() => { setStep(0); setResult(null); setUploadedFiles([]); setKeyColumns([]); }} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">🔄 Làm lại</button>
              <button onClick={handleExport} className="px-6 py-2.5 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors">📥 Xuất Excel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
