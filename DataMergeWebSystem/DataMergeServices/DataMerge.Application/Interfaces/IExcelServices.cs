using DataMerge.Domain.Models;

namespace DataMerge.Application.Interfaces
{
    public interface IExcelService
    {
        /// <summary>Đọc header + preview n dòng đầu của file Excel.</summary>
        Task<ExcelFileStructure> ReadStructureAsync(string filePath, string? sheetName = null);

        /// <summary>Đọc toàn bộ dữ liệu của file Excel thành danh sách dictionary.</summary>
        Task<List<Dictionary<string, object?>>> ReadAllDataAsync(string filePath, string? sheetName = null);

        /// <summary>Ghi danh sách dictionary ra file Excel, trả về byte[].</summary>
        Task<byte[]> WriteToExcelAsync(List<Dictionary<string, object?>> data, string sheetName = "Sheet1");
    }

    public interface IMergeService
    {
        /// <summary>Gộp nhiều file dữ liệu theo các key columns đã cấu hình.</summary>
        Task<MergeResultDto> MergeFilesAsync(List<string> filePaths, MergeKeyConfig config);

        /// <summary>Left Join: gắn thêm cột từ file phụ vào file gốc theo mapping.</summary>
        Task<MergeResultDto> LeftJoinAsync(
            string masterFilePath,
            List<string> auxFilePaths,
            List<ColumnMappingItem> mappings,
            List<string> keyColumns,
            Dictionary<string, string>? selectedSheetByFile = null);
    }

    public interface IGoodsMatcherService
    {
        /// <summary>So khớp dữ liệu input với catalog, trả về kết quả phân loại.</summary>
        Task<GoodsMatchResult> MatchAsync(string inputFilePath, string catalogFilePath, string matchColumn);

        /// <summary>Xuất kết quả đã được duyệt ra file Excel.</summary>
        Task<byte[]> ExportApprovedAsync(GoodsMatchResult result);
    }

    public interface IFileUploadService
    {
        /// <summary>Lưu file upload lên server, trả về đường dẫn tạm thời.</summary>
        Task<string> SaveTempFileAsync(Stream fileStream, string fileName);

        /// <summary>Lấy đường dẫn đầy đủ từ fileId tạm.</summary>
        string GetTempFilePath(string fileId);

        void CleanupTempFile(string fileId);
    }
}
