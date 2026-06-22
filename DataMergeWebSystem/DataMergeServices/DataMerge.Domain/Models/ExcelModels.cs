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
        public int TotalRows { get; set; }
    }

    /// <summary>
    /// Cấu hình khóa gộp dữ liệu (Unified Key Config).
    /// </summary>
    public class MergeKeyConfig
    {
        /// <summary>Key: đường dẫn file, Value: danh sách tên cột được chọn làm khóa</summary>
        public Dictionary<string, List<string>> KeyColumnsByFile { get; set; } = new();
        public int MergeMode { get; set; } // 1: Union/Dedup, 2: LeftJoin, 3: Clean Only
    }

    /// <summary>
    /// Kết quả gộp dữ liệu trả về cho FE.
    /// </summary>
    public class MergeResultDto
    {
        public List<Dictionary<string, object?>> Rows { get; set; } = new();
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
