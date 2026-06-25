import { useState, useCallback, useEffect } from 'react';
import { Upload, FileSpreadsheet, CheckCircle, Loader, X } from 'lucide-react';
import { uploadFile } from '../../services/excelService';

/**
 * Component Upload file Excel. Hỗ trợ kéo thả (drag & drop) và chọn file thông thường.
 * Sau khi upload thành công, trả về { fileId, fileName, headers, totalRows } qua onUploadSuccess.
 */
export default function FileUploader({ onUploadSuccess, onRemove, label = "Chọn file Excel", initialFile = null }) {
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(initialFile);
  const [error, setError] = useState('');

  const handleRemove = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setUploadedFile(null);
    onRemove?.();
  };

  useEffect(() => {
    if (initialFile) {
      setUploadedFile({ name: initialFile.fileName || initialFile.name, ...initialFile });
    } else {
      setUploadedFile(null);
    }
  }, [initialFile]);

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      setError('Chỉ chấp nhận file Excel (.xlsx, .xls)');
      return;
    }

    setError('');
    setLoading(true);
    try {
      const res = await uploadFile(file);
      const structure = res.data;
      setUploadedFile({ name: file.name, ...structure });
      onUploadSuccess?.({ 
        ...structure,
        fileId: structure.filePath, 
        fileName: file.name 
      });
    } catch (err) {
      console.error('Upload error:', err);
      let errorMsg = 'Upload thất bại. Vui lòng thử lại.';
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          if (err.response.data.toLowerCase().includes('<html')) {
            errorMsg = `Lỗi hệ thống (${err.response.status}). Vui lòng kiểm tra file hoặc báo admin.`;
          } else {
            errorMsg = err.response.data;
          }
        } else if (err.response.data.message) {
          errorMsg = err.response.data.message;
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [onUploadSuccess]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const handleInputChange = (e) => handleFile(e.target.files[0]);

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging ? 'border-blue-500 bg-blue-50' : 
          uploadedFile ? 'border-green-400 bg-green-50' : 
          'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50/30'
        }`}
      >
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
          disabled={loading}
        />
        {uploadedFile && (
          <button
            onClick={handleRemove}
            className="absolute top-3 right-3 p-1.5 bg-red-100 text-red-600 rounded-full hover:bg-red-200 transition-colors z-20 cursor-pointer"
            title="Xóa file này"
          >
            <X size={18} />
          </button>
        )}
        <div className="flex flex-col items-center space-y-2 relative z-0">
          {loading ? (
            <Loader size={40} className="text-blue-500 animate-spin" />
          ) : uploadedFile ? (
            <CheckCircle size={40} className="text-green-500" />
          ) : (
            <FileSpreadsheet size={40} className={isDragging ? 'text-blue-500' : 'text-gray-400'} />
          )}
          <div className="text-sm">
            {loading ? (
              <span className="text-blue-600 font-medium">Đang upload...</span>
            ) : uploadedFile ? (
              <div className="text-green-700">
                <p className="font-semibold">{uploadedFile.name}</p>
                <p className="text-xs text-green-600">{uploadedFile.totalRows} dòng · {uploadedFile.headers?.length} cột</p>
              </div>
            ) : (
              <>
                <span className="font-semibold text-blue-600 cursor-pointer">Nhấn để chọn file</span>
                <span className="text-gray-500"> hoặc kéo thả vào đây</span>
                <p className="text-xs text-gray-400 mt-1">Hỗ trợ: .xlsx, .xls (tối đa 100MB)</p>
              </>
            )}
          </div>
        </div>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
