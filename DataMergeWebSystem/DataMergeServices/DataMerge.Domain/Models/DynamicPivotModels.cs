namespace DataMerge.Domain.Models
{
    public class PivotAnalyzeRequest
    {
        public string FileId { get; set; } = string.Empty;
        public string? SheetName { get; set; }
        public List<string> SourceColumns { get; set; } = new();
        public bool IgnoreCase { get; set; } = true;
        public string? MultiValueSeparator { get; set; } // ",", ";", "/" hoặc rỗng
    }

    public class PivotUniqueValueDto
    {
        public string OriginalValue { get; set; } = string.Empty;
        public int Count { get; set; }
        public string TargetColumnName { get; set; } = string.Empty;
        public bool IsSelected { get; set; } = true;
    }

    public class PivotColumnAnalysis
    {
        public string SourceColumn { get; set; } = string.Empty;
        public List<PivotUniqueValueDto> UniqueValues { get; set; } = new();
        public string? WarningMessage { get; set; }
    }

    public class PivotAnalyzeResult
    {
        public int TotalRows { get; set; }
        public List<PivotColumnAnalysis> ColumnsAnalysis { get; set; } = new();
    }

    public class PivotMappingRule
    {
        public string OriginalValue { get; set; } = string.Empty;
        public string TargetColumnName { get; set; } = string.Empty;
        public bool IsSelected { get; set; } = true;
    }

    public class PivotColumnConfig
    {
        public string SourceColumn { get; set; } = string.Empty;
        public List<PivotMappingRule> Mappings { get; set; } = new();
        public string EmptyRowHandling { get; set; } = "Ignore"; // "Ignore", "Unspecified", "Other"
        public string UnspecifiedColumnName { get; set; } = "Chưa xác định";
        public string OtherColumnName { get; set; } = "Khác";
    }

    public class PivotExecuteConfig
    {
        public string FileId { get; set; } = string.Empty;
        public string? SheetName { get; set; }
        public List<PivotColumnConfig> ColumnConfigs { get; set; } = new();
        public string MarkSymbol { get; set; } = "x"; // "x", "✓", "1", "Original"
        public string Placement { get; set; } = "Replace"; // "Replace", "AfterSource", "End"
        public string? MultiValueSeparator { get; set; }
        public bool IgnoreCase { get; set; } = true;
    }

    public class PivotPreviewResult
    {
        public List<string> Headers { get; set; } = new();
        public List<Dictionary<string, object?>> PreviewRows { get; set; } = new();
        public int TotalRows { get; set; }
        public Dictionary<string, int> ColumnStats { get; set; } = new();
    }
}
