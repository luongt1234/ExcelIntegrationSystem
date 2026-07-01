namespace DataMerge.Domain.Models
{
    /// <summary>
    /// Kết quả phân tích cấu trúc một file Excel.
    /// </summary>
    public class ExcelFileStructure
    {
        public string FilePath { get; set; } = string.Empty;
        public string FileName { get; set; } = string.Empty;
        public List<string> Headers { get; set; } = new();
        public List<List<HeaderCellDto>> HeaderGrid { get; set; } = new();
        public int TotalRows { get; set; }
        public List<string> SheetNames { get; set; } = new();
        public string SelectedSheet { get; set; } = string.Empty;
    }

    /// <summary>
    /// Biểu diễn một ô Tiêu đề (có thể bị Merge) trong lưới Header 2D.
    /// </summary>
    public class HeaderCellDto
    {
        public string Text { get; set; } = string.Empty;
        public int RowSpan { get; set; } = 1;
        public int ColSpan { get; set; } = 1;
        // Danh sách các chỉ số cột (0-based) mà ô này bao trùm
        public List<int> CoveredColumns { get; set; } = new();
    }

    /// <summary>
    /// Cấu hình khóa gộp dữ liệu (Unified Key Config).
    /// </summary>
    public class MergeKeyConfig
    {
        /// <summary>Key: đường dẫn file, Value: danh sách tên cột được chọn làm khóa</summary>
        public Dictionary<string, List<string>> KeyColumnsByFile { get; set; } = new();
        public int MergeMode { get; set; } // 1: Union/Dedup, 2: LeftJoin, 3: Clean Only
        
        /// <summary>Key: fileId (không phải filePath), Value: Dictionary ánh xạ tên cột cũ -> tên cột mới</summary>
        public Dictionary<string, Dictionary<string, string>>? ColumnMappingsByFile { get; set; }
        
        /// <summary>Key: fileId, Value: tên sheet được chọn</summary>
        public Dictionary<string, string>? SelectedSheetByFile { get; set; }

        /// <summary>Key: filePath, Value: tên file gốc dễ đọc cho người dùng</summary>
        public Dictionary<string, string>? FileNamesByPath { get; set; }
    }

    public class RemovedDuplicateDto
    {
        public Dictionary<string, object?> RemovedRow { get; set; } = new();
        public Dictionary<string, object?> KeptRow { get; set; } = new();
        public string SourceFile { get; set; } = string.Empty;
        public int SourceRowIndex { get; set; }
        public string MatchedKey { get; set; } = string.Empty;
        public int KeptRowIndex { get; set; }
    }

    /// <summary>
    /// Kết quả gộp dữ liệu trả về cho FE.
    /// </summary>
    public class MergeResultDto
    {
        public List<Dictionary<string, object?>> Rows { get; set; } = new();
        public List<RemovedDuplicateDto> RemovedDuplicates { get; set; } = new();
        public List<string> Headers { get; set; } = new();
        public int TotalInput { get; set; }
        public int TotalOutput { get; set; }
        public int TotalDuplicate { get; set; }
    }

    /// <summary>
    /// Cấu hình ghép cột cho Left Join (Drag & Drop Mapping).
    /// </summary>
    public class ColumnMappingItem
    {
        public string MasterColumn { get; set; } = string.Empty;
        public string AuxFile { get; set; } = string.Empty;
        public string AuxColumn { get; set; } = string.Empty;
        public string OutputColumnName { get; set; } = string.Empty;
    }

    /// <summary>
    /// Yêu cầu Left Join.
    /// </summary>
    public class LeftJoinRequest
    {
        public string MasterFileId { get; set; } = string.Empty;
        public List<string> AuxFileIds { get; set; } = new();
        public List<ColumnMappingItem> Mappings { get; set; } = new();
        public List<string> KeyColumns { get; set; } = new();
        public Dictionary<string, string>? SelectedSheetByFile { get; set; }
    }

    /// <summary>
    /// Một dòng dữ liệu Hàng hóa với trạng thái xét duyệt.
    /// </summary>
    public class GoodsItem
    {
        public int OriginalRowIndex { get; set; }
        public Dictionary<string, object?> InputData { get; set; } = new();
        public Dictionary<string, object?> CatalogData { get; set; } = new();
        public double MatchScore { get; set; }
        public string Status { get; set; } = "Pending"; // "Approved", "Pending", "Rejected"
        public string MatchedKey { get; set; } = string.Empty;
    }

    /// <summary>
    /// Kết quả từ Goods Matcher.
    /// </summary>
    public class GoodsMatchResult
    {
        public List<GoodsItem> Approved { get; set; } = new();
        public List<GoodsItem> Pending { get; set; } = new();
        public List<GoodsItem> Rejected { get; set; } = new();
    }
}
