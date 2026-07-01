using DataMerge.Domain.Models;

namespace DataMerge.Application.Interfaces
{
    public interface IDynamicPivotService
    {
        Task<PivotAnalyzeResult> AnalyzeAsync(string filePath, PivotAnalyzeRequest request);
        Task<PivotPreviewResult> PreviewAsync(string filePath, PivotExecuteConfig config);
        Task<byte[]> ExportAsync(string filePath, PivotExecuteConfig config);
        Task<PivotPreviewResult> UnpivotPreviewAsync(string filePath, UnpivotRequest request);
        Task<byte[]> UnpivotExportAsync(string filePath, UnpivotRequest request);
    }
}
