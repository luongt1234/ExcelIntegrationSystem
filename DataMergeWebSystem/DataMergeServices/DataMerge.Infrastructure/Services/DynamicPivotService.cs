using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;

namespace DataMerge.Infrastructure.Services
{
    public class DynamicPivotService : IDynamicPivotService
    {
        private readonly IExcelService _excelService;

        public DynamicPivotService(IExcelService excelService)
        {
            _excelService = excelService;
        }

        public async Task<PivotAnalyzeResult> AnalyzeAsync(string filePath, PivotAnalyzeRequest request)
        {
            var allRows = await _excelService.ReadAllDataAsync(filePath, request.SheetName);
            var result = new PivotAnalyzeResult
            {
                TotalRows = allRows.Count
            };

            foreach (var colName in request.SourceColumns)
            {
                var analysis = new PivotColumnAnalysis { SourceColumn = colName };
                var valueCounts = new Dictionary<string, (string originalText, int count)>(request.IgnoreCase ? StringComparer.OrdinalIgnoreCase : StringComparer.Ordinal);

                foreach (var row in allRows)
                {
                    if (!row.TryGetValue(colName, out var rawVal) || rawVal == null)
                        continue;

                    var strVal = rawVal.ToString()?.Trim();
                    if (string.IsNullOrEmpty(strVal))
                        continue;

                    var tokens = new List<string>();
                    if (!string.IsNullOrEmpty(request.MultiValueSeparator) && strVal.Contains(request.MultiValueSeparator))
                    {
                        tokens.AddRange(strVal.Split(new[] { request.MultiValueSeparator }, StringSplitOptions.RemoveEmptyEntries).Select(t => t.Trim()).Where(t => !string.IsNullOrEmpty(t)));
                    }
                    else
                    {
                        tokens.Add(strVal);
                    }

                    foreach (var token in tokens)
                    {
                        if (valueCounts.TryGetValue(token, out var existing))
                        {
                            valueCounts[token] = (existing.originalText, existing.count + 1);
                        }
                        else
                        {
                            valueCounts[token] = (token, 1);
                        }
                    }
                }

                foreach (var kvp in valueCounts.OrderByDescending(x => x.Value.count))
                {
                    analysis.UniqueValues.Add(new PivotUniqueValueDto
                    {
                        OriginalValue = kvp.Value.originalText,
                        TargetColumnName = kvp.Value.originalText,
                        Count = kvp.Value.count,
                        IsSelected = true
                    });
                }

                if (analysis.UniqueValues.Count > 20)
                {
                    analysis.WarningMessage = $"Cột '{colName}' có {analysis.UniqueValues.Count} giá trị khác nhau. Bạn có chắc muốn tách thành {analysis.UniqueValues.Count} cột?";
                }

                result.ColumnsAnalysis.Add(analysis);
            }

            return result;
        }

        public async Task<PivotPreviewResult> PreviewAsync(string filePath, PivotExecuteConfig config)
        {
            var allRows = await _excelService.ReadAllDataAsync(filePath, config.SheetName);
            var (newHeaders, pivotedRows, stats) = ExecutePivotInternal(allRows, config);

            var previewRows = pivotedRows.Take(15).ToList();

            return new PivotPreviewResult
            {
                Headers = newHeaders,
                PreviewRows = previewRows,
                TotalRows = pivotedRows.Count,
                ColumnStats = stats
            };
        }

        public async Task<byte[]> ExportAsync(string filePath, PivotExecuteConfig config)
        {
            var allRows = await _excelService.ReadAllDataAsync(filePath, config.SheetName);
            var (newHeaders, pivotedRows, _) = ExecutePivotInternal(allRows, config);

            return await _excelService.WriteToExcelAsync(pivotedRows, "DynamicPivotResult");
        }

        private (List<string> headers, List<Dictionary<string, object?>> rows, Dictionary<string, int> stats) ExecutePivotInternal(
            List<Dictionary<string, object?>> allRows, PivotExecuteConfig config)
        {
            var stats = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);

            // 1. Xác định danh sách cột gốc ban đầu
            var originalHeaders = new List<string>();
            if (allRows.Count > 0)
            {
                originalHeaders = allRows[0].Keys.ToList();
            }

            // 2. Chuẩn bị ánh xạ TargetColumnName hợp lệ và không trùng lặp
            var targetColNamesPerSource = new Dictionary<string, List<string>>();
            var allTargetNamesWithSource = new List<(string sourceCol, string targetName)>();

            foreach (var colCfg in config.ColumnConfigs)
            {
                var listCols = new List<string>();
                var selectedMappings = colCfg.Mappings.Where(m => m.IsSelected && !string.IsNullOrWhiteSpace(m.TargetColumnName)).ToList();

                foreach (var grp in selectedMappings.GroupBy(m => m.TargetColumnName, config.IgnoreCase ? StringComparer.OrdinalIgnoreCase : StringComparer.Ordinal))
                {
                    var tName = grp.Key.Trim();
                    if (!listCols.Contains(tName, StringComparer.OrdinalIgnoreCase))
                    {
                        listCols.Add(tName);
                        allTargetNamesWithSource.Add((colCfg.SourceColumn, tName));
                    }
                }

                if (colCfg.EmptyRowHandling == "Unspecified" && !string.IsNullOrWhiteSpace(colCfg.UnspecifiedColumnName))
                {
                    var tName = colCfg.UnspecifiedColumnName.Trim();
                    if (!listCols.Contains(tName, StringComparer.OrdinalIgnoreCase))
                    {
                        listCols.Add(tName);
                        allTargetNamesWithSource.Add((colCfg.SourceColumn, tName));
                    }
                }

                if (colCfg.EmptyRowHandling == "Other" && !string.IsNullOrWhiteSpace(colCfg.OtherColumnName))
                {
                    var tName = colCfg.OtherColumnName.Trim();
                    if (!listCols.Contains(tName, StringComparer.OrdinalIgnoreCase))
                    {
                        listCols.Add(tName);
                        allTargetNamesWithSource.Add((colCfg.SourceColumn, tName));
                    }
                }

                targetColNamesPerSource[colCfg.SourceColumn] = listCols;
            }

            // Kiểm tra trùng tên cột mới giữa các cột gốc khác nhau
            var dupTargetNamesAcrossSources = allTargetNamesWithSource
                .GroupBy(x => x.targetName, StringComparer.OrdinalIgnoreCase)
                .Where(g => g.Select(x => x.sourceCol).Distinct().Count() > 1)
                .Select(g => g.Key)
                .ToHashSet(StringComparer.OrdinalIgnoreCase);

            // Phân giải tên cột cuối cùng cho từng (sourceCol, targetName)
            var resolvedTargetNames = new Dictionary<(string sourceCol, string targetName), string>();
            var usedHeaders = new HashSet<string>(originalHeaders.Where(h => config.Placement != "Replace" || !config.ColumnConfigs.Any(c => c.SourceColumn.Equals(h, StringComparison.OrdinalIgnoreCase))), StringComparer.OrdinalIgnoreCase);

            foreach (var colCfg in config.ColumnConfigs)
            {
                if (!targetColNamesPerSource.TryGetValue(colCfg.SourceColumn, out var rawTargets))
                    continue;

                foreach (var rawTarget in rawTargets)
                {
                    string candidate = rawTarget;
                    if (dupTargetNamesAcrossSources.Contains(rawTarget))
                    {
                        candidate = $"{colCfg.SourceColumn} - {rawTarget}";
                    }

                    string finalName = candidate;
                    int counter = 2;
                    while (usedHeaders.Contains(finalName))
                    {
                        finalName = $"{candidate} ({counter++})";
                    }

                    usedHeaders.Add(finalName);
                    resolvedTargetNames[(colCfg.SourceColumn, rawTarget)] = finalName;
                    stats[finalName] = 0;
                }
            }

            // 3. Tạo danh sách Header mới theo Placement
            var finalHeaders = new List<string>();
            if (config.Placement == "Replace")
            {
                foreach (var h in originalHeaders)
                {
                    var colCfg = config.ColumnConfigs.FirstOrDefault(c => c.SourceColumn.Equals(h, StringComparison.OrdinalIgnoreCase));
                    if (colCfg != null)
                    {
                        if (targetColNamesPerSource.TryGetValue(colCfg.SourceColumn, out var rawTargets))
                        {
                            foreach (var raw in rawTargets)
                            {
                                if (resolvedTargetNames.TryGetValue((colCfg.SourceColumn, raw), out var resolved))
                                {
                                    if (!finalHeaders.Contains(resolved)) finalHeaders.Add(resolved);
                                }
                            }
                        }
                    }
                    else
                    {
                        finalHeaders.Add(h);
                    }
                }
            }
            else if (config.Placement == "AfterSource")
            {
                foreach (var h in originalHeaders)
                {
                    finalHeaders.Add(h);
                    var colCfg = config.ColumnConfigs.FirstOrDefault(c => c.SourceColumn.Equals(h, StringComparison.OrdinalIgnoreCase));
                    if (colCfg != null)
                    {
                        if (targetColNamesPerSource.TryGetValue(colCfg.SourceColumn, out var rawTargets))
                        {
                            foreach (var raw in rawTargets)
                            {
                                if (resolvedTargetNames.TryGetValue((colCfg.SourceColumn, raw), out var resolved))
                                {
                                    if (!finalHeaders.Contains(resolved)) finalHeaders.Add(resolved);
                                }
                            }
                        }
                    }
                }
            }
            else // "End"
            {
                finalHeaders.AddRange(originalHeaders);
                foreach (var colCfg in config.ColumnConfigs)
                {
                    if (targetColNamesPerSource.TryGetValue(colCfg.SourceColumn, out var rawTargets))
                    {
                        foreach (var raw in rawTargets)
                        {
                            if (resolvedTargetNames.TryGetValue((colCfg.SourceColumn, raw), out var resolved))
                            {
                                if (!finalHeaders.Contains(resolved)) finalHeaders.Add(resolved);
                            }
                        }
                    }
                }
            }

            // 4. Xử lý từng dòng dữ liệu
            var pivotedRows = new List<Dictionary<string, object?>>();
            var comparer = config.IgnoreCase ? StringComparer.OrdinalIgnoreCase : StringComparer.Ordinal;

            foreach (var row in allRows)
            {
                var newRow = new Dictionary<string, object?>();

                // Gán giá trị ban đầu cho các cột trong finalHeaders (nếu từ originalHeaders thì copy, nếu là cột pivot thì để null)
                foreach (var fh in finalHeaders)
                {
                    if (row.TryGetValue(fh, out var origVal))
                    {
                        newRow[fh] = origVal;
                    }
                    else
                    {
                        newRow[fh] = null;
                    }
                }

                // Xử lý Pivot cho các cột được cấu hình
                foreach (var colCfg in config.ColumnConfigs)
                {
                    row.TryGetValue(colCfg.SourceColumn, out var rawVal);
                    var strVal = rawVal?.ToString()?.Trim();

                    if (config.Placement == "Replace")
                    {
                        newRow.Remove(colCfg.SourceColumn);
                    }

                    if (string.IsNullOrEmpty(strVal))
                    {
                        if (colCfg.EmptyRowHandling == "Unspecified" && !string.IsNullOrWhiteSpace(colCfg.UnspecifiedColumnName))
                        {
                            if (resolvedTargetNames.TryGetValue((colCfg.SourceColumn, colCfg.UnspecifiedColumnName.Trim()), out var resolvedCol))
                            {
                                newRow[resolvedCol] = GetMarkValue(config.MarkSymbol, "Chưa xác định");
                                stats[resolvedCol] = (stats.TryGetValue(resolvedCol, out var cur) ? cur : 0) + 1;
                            }
                        }
                        else if (colCfg.EmptyRowHandling == "Other" && !string.IsNullOrWhiteSpace(colCfg.OtherColumnName))
                        {
                            if (resolvedTargetNames.TryGetValue((colCfg.SourceColumn, colCfg.OtherColumnName.Trim()), out var resolvedCol))
                            {
                                newRow[resolvedCol] = GetMarkValue(config.MarkSymbol, "Khác");
                                stats[resolvedCol] = (stats.TryGetValue(resolvedCol, out var cur) ? cur : 0) + 1;
                            }
                        }
                        continue;
                    }

                    var tokens = new List<string>();
                    if (!string.IsNullOrEmpty(config.MultiValueSeparator) && strVal.Contains(config.MultiValueSeparator))
                    {
                        tokens.AddRange(strVal.Split(new[] { config.MultiValueSeparator }, StringSplitOptions.RemoveEmptyEntries).Select(t => t.Trim()).Where(t => !string.IsNullOrEmpty(t)));
                    }
                    else
                    {
                        tokens.Add(strVal);
                    }

                    bool anyTokenMatched = false;
                    foreach (var token in tokens)
                    {
                        // Tìm mapping tương ứng cho token này
                        var matchedMap = colCfg.Mappings.FirstOrDefault(m => m.IsSelected && comparer.Equals(m.OriginalValue.Trim(), token));
                        if (matchedMap != null && !string.IsNullOrWhiteSpace(matchedMap.TargetColumnName))
                        {
                            anyTokenMatched = true;
                            if (resolvedTargetNames.TryGetValue((colCfg.SourceColumn, matchedMap.TargetColumnName.Trim()), out var resolvedCol))
                            {
                                newRow[resolvedCol] = GetMarkValue(config.MarkSymbol, token);
                                stats[resolvedCol] = (stats.TryGetValue(resolvedCol, out var cur) ? cur : 0) + 1;
                            }
                        }
                    }

                    if (!anyTokenMatched && colCfg.EmptyRowHandling == "Other" && !string.IsNullOrWhiteSpace(colCfg.OtherColumnName))
                    {
                        if (resolvedTargetNames.TryGetValue((colCfg.SourceColumn, colCfg.OtherColumnName.Trim()), out var resolvedCol))
                        {
                            newRow[resolvedCol] = GetMarkValue(config.MarkSymbol, strVal);
                            stats[resolvedCol] = (stats.TryGetValue(resolvedCol, out var cur) ? cur : 0) + 1;
                        }
                    }
                }

                pivotedRows.Add(newRow);
            }

            return (finalHeaders, pivotedRows, stats);
        }

        private static string GetMarkValue(string symbol, string fallbackOriginal)
        {
            if (string.Equals(symbol, "Original", StringComparison.OrdinalIgnoreCase))
                return fallbackOriginal;
            return symbol;
        }
    }
}
