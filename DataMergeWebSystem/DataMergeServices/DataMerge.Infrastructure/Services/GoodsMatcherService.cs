using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;

namespace DataMerge.Infrastructure.Services
{
    /// <summary>
    /// Hiện thực logic Gộp Hàng Hóa (Catalog Matcher).
    /// Port từ Python services/goods_processor.py sang C#.
    /// Sử dụng thuật toán so khớp chuỗi đơn giản (Token overlap).
    /// </summary>
    public class GoodsMatcherService : IGoodsMatcherService
    {
        private readonly IExcelService _excelService;
        private const double AutoApproveThreshold = 0.85;
        private const double PendingThreshold = 0.50;

        public GoodsMatcherService(IExcelService excelService)
        {
            _excelService = excelService;
        }

        public async Task<GoodsMatchResult> MatchAsync(
            string inputFilePath,
            string catalogFilePath,
            string matchColumn)
        {
            var inputData = await _excelService.ReadAllDataAsync(inputFilePath);
            var catalogData = await _excelService.ReadAllDataAsync(catalogFilePath);

            var result = new GoodsMatchResult();

            // Xây dựng catalog lookup
            var catalogItems = catalogData
                .Select(row => new
                {
                    Key = row.TryGetValue(matchColumn, out var v) ? NormalizeText(v?.ToString() ?? "") : "",
                    Data = row
                })
                .Where(x => !string.IsNullOrEmpty(x.Key))
                .ToList();

            for (int i = 0; i < inputData.Count; i++)
            {
                var inputRow = inputData[i];
                var inputText = inputRow.TryGetValue(matchColumn, out var iv) ? NormalizeText(iv?.ToString() ?? "") : "";

                // Tìm catalog item phù hợp nhất
                var bestMatch = catalogItems
                    .Select(ci => new { ci.Key, ci.Data, Score = ComputeTokenOverlap(inputText, ci.Key) })
                    .OrderByDescending(x => x.Score)
                    .FirstOrDefault();

                var item = new GoodsItem
                {
                    OriginalRowIndex = i,
                    InputData = inputRow,
                    CatalogData = bestMatch?.Data ?? new Dictionary<string, object?>(),
                    MatchScore = bestMatch?.Score ?? 0,
                    MatchedKey = bestMatch?.Key ?? ""
                };

                if (bestMatch?.Score >= AutoApproveThreshold)
                {
                    item.Status = "Approved";
                    result.Approved.Add(item);
                }
                else if (bestMatch?.Score >= PendingThreshold)
                {
                    item.Status = "Pending";
                    result.Pending.Add(item);
                }
                else
                {
                    item.Status = "Rejected";
                    result.Rejected.Add(item);
                }
            }

            return result;
        }

        public async Task<byte[]> ExportApprovedAsync(GoodsMatchResult result)
        {
            var exportData = result.Approved
                .Select(item =>
                {
                    var row = new Dictionary<string, object?>(item.InputData);
                    foreach (var kv in item.CatalogData)
                        row[$"[Catalog] {kv.Key}"] = kv.Value;
                    row["Match Score"] = $"{item.MatchScore:P0}";
                    return row;
                })
                .ToList();

            return await _excelService.WriteToExcelAsync(exportData, "Approved");
        }

        private static string NormalizeText(string text)
        {
            return text.ToLowerInvariant().Trim();
        }

        /// <summary>
        /// Token Overlap Score: tỷ lệ token của input xuất hiện trong catalog key.
        /// </summary>
        private static double ComputeTokenOverlap(string a, string b)
        {
            if (string.IsNullOrEmpty(a) || string.IsNullOrEmpty(b)) return 0;

            var tokensA = a.Split(new[] { ' ', '-', '_', '/', '.' }, StringSplitOptions.RemoveEmptyEntries).ToHashSet();
            var tokensB = b.Split(new[] { ' ', '-', '_', '/', '.' }, StringSplitOptions.RemoveEmptyEntries).ToHashSet();

            if (!tokensA.Any()) return 0;

            double intersection = tokensA.Count(t => tokensB.Contains(t));
            double union = tokensA.Union(tokensB).Count();

            return intersection / union; // Jaccard similarity
        }
    }
}
