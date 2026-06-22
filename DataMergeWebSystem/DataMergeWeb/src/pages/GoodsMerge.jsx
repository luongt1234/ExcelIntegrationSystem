import { useState } from 'react';
import { Package, Check, ArrowRight, CheckCircle, XCircle, Clock } from 'lucide-react';
import FileUploader from '../components/FileUploader/FileUploader';
import BaseTable from '../components/BaseTable/BaseTable';
import { matchGoods, exportGoodsResult, downloadBlob } from '../services/excelService';

const TABS = [
  { key: 'Approved', label: 'Đã duyệt', icon: <CheckCircle size={16} />, color: 'text-green-600', bg: 'bg-green-50 border-green-200', activeBtn: 'bg-green-600' },
  { key: 'Pending', label: 'Chờ duyệt', icon: <Clock size={16} />, color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200', activeBtn: 'bg-yellow-500' },
  { key: 'Rejected', label: 'Từ chối', icon: <XCircle size={16} />, color: 'text-red-600', bg: 'bg-red-50 border-red-200', activeBtn: 'bg-red-600' },
];

export default function GoodsMerge() {
  const [step, setStep] = useState(0);
  const [inputFile, setInputFile] = useState(null);
  const [catalogFile, setCatalogFile] = useState(null);
  const [matchColumn, setMatchColumn] = useState('');
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('Pending');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleMatch = async () => {
    if (!inputFile || !catalogFile) { setError('Cần chọn cả 2 file.'); return; }
    if (!matchColumn) { setError('Cần chọn cột để so khớp.'); return; }
    setError('');
    setLoading(true);
    try {
      const res = await matchGoods(inputFile.fileId, catalogFile.fileId, matchColumn);
      setResult(res.data);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.message || 'Xử lý thất bại.');
    } finally {
      setLoading(false);
    }
  };

  const moveItem = (item, from, to) => {
    setResult(prev => {
      const updated = { ...prev };
      updated[from] = updated[from].filter(i => i.originalRowIndex !== item.originalRowIndex);
      updated[to] = [...updated[to], { ...item, status: to }];
      return updated;
    });
  };

  const handleExport = async () => {
    const res = await exportGoodsResult(result);
    downloadBlob(res, 'KetQua_HangHoa.xlsx');
  };

  const buildColumns = (items) => {
    if (!items?.length) return [];
    const keys = [...new Set([
      ...Object.keys(items[0].inputData ?? {}),
      ...Object.keys(items[0].catalogData ?? {}),
    ])];
    return keys.map(k => ({ Header: k, accessor: k }));
  };

  const buildRows = (items) =>
    (items ?? []).map(item => ({
      ...item.inputData,
      ...Object.fromEntries(Object.entries(item.catalogData ?? {}).map(([k, v]) => [`[Cat] ${k}`, v])),
      'Match Score': `${((item.matchScore ?? 0) * 100).toFixed(0)}%`,
    }));

  const currentItems = result?.[activeTab] ?? [];
  const currentTab = TABS.find(t => t.key === activeTab);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
        <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center"><Package size={24} /></div>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Gộp Hàng Hóa</h1>
          <p className="text-gray-500">So khớp dữ liệu Input với Danh mục (Catalog), phân loại và xét duyệt.</p>
        </div>
      </div>

      {step < 2 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FileUploader label="File Input (dữ liệu cần khớp)" onUploadSuccess={setInputFile} />
            <FileUploader label="File Catalog (danh mục chuẩn)" onUploadSuccess={setCatalogFile} />
          </div>

          {(inputFile?.headers?.length > 0 || catalogFile?.headers?.length > 0) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Chọn cột để so khớp</label>
              <select
                value={matchColumn}
                onChange={e => setMatchColumn(e.target.value)}
                className="w-full md:w-64 px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 text-sm"
              >
                <option value="">-- Chọn cột khóa --</option>
                {(inputFile?.headers ?? []).map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end">
            <button onClick={handleMatch} disabled={loading} className="px-8 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center space-x-2">
              {loading ? <><span className="animate-spin">⏳</span><span>Đang phân tích...</span></> : <span>🔍 Bắt đầu So khớp</span>}
            </button>
          </div>
        </div>
      )}

      {step === 2 && result && (
        <div className="space-y-4">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            {TABS.map(t => (
              <div key={t.key} className={`rounded-xl p-4 text-center border ${t.bg}`}>
                <div className={`text-3xl font-bold ${t.color}`}>{result[t.key]?.length ?? 0}</div>
                <div className={`text-sm font-medium mt-1 flex items-center justify-center space-x-1 ${t.color}`}>
                  {t.icon}<span>{t.label}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="flex border-b border-gray-200 bg-gray-50">
              {TABS.map(t => (
                <button key={t.key} onClick={() => setActiveTab(t.key)}
                  className={`flex-1 flex items-center justify-center space-x-2 py-3 text-sm font-semibold transition-colors ${
                    activeTab === t.key ? `${t.color} border-b-2 border-current bg-white` : 'text-gray-500 hover:text-gray-700'
                  }`}>
                  {t.icon}<span>{t.label} ({result[t.key]?.length ?? 0})</span>
                </button>
              ))}
            </div>

            <div className="p-4">
              <BaseTable
                columns={buildColumns(currentItems)}
                data={buildRows(currentItems)}
                title={`Danh sách ${currentTab?.label}`}
                enableExport={false}
              />

              {/* Action buttons per tab */}
              {activeTab === 'Pending' && currentItems.length > 0 && (
                <div className="mt-3 text-sm text-gray-500">
                  💡 Chọn dòng và dùng nút bên dưới để phân loại thủ công (chức năng nâng cao).
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-between">
            <button onClick={() => { setStep(0); setResult(null); }} className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">🔄 Làm lại</button>
            <button onClick={handleExport} className="px-6 py-2.5 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors">📥 Xuất Excel Đã duyệt</button>
          </div>
        </div>
      )}
    </div>
  );
}
