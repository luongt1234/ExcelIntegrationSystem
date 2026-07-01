using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;

namespace DataMerge.Infrastructure.Services
{
    /// <summary>
    /// Hiện thực logic Gộp Hồ Sơ (Dedup + Union) và Bổ sung thông tin (Left Join).
    /// Port từ Python services/data_processor.py sang C#.
    /// </summary>
    public class MergeService : IMergeService
    {
        private readonly IExcelService _excelService;

        public MergeService(IExcelService excelService)
        {
            _excelService = excelService;
        }

        /// <summary>
        /// Gộp nhiều file theo Unified Key Config.
        /// - Mode 1: Union + Dedup (loại trùng lặp theo key).
        /// - Mode 3: Chỉ dọn dẹp / chuẩn hóa 1 file (không gộp).
        /// </summary>
        private class RowWithMetadata
        {
            public Dictionary<string, object?> Row { get; set; } = new();
            public string SourceFile { get; set; } = string.Empty;
            public int RowIndex { get; set; }
        }

        public async Task<MergeResultDto> MergeFilesAsync(List<string> filePaths, MergeKeyConfig config)
        {
            var allData = new List<RowWithMetadata>();
            int totalInput = 0;

            // Đọc toàn bộ data từ các files
            foreach (var fp in filePaths)
            {
                string? selectedSheet = null;
                if (config.SelectedSheetByFile != null && config.SelectedSheetByFile.TryGetValue(fp, out var sheet))
                {
                    selectedSheet = sheet;
                }

                string sourceFile = Path.GetFileName(fp);
                if (config.FileNamesByPath != null && config.FileNamesByPath.TryGetValue(fp, out var fn) && !string.IsNullOrWhiteSpace(fn))
                {
                    sourceFile = fn;
                }

                var fileData = await _excelService.ReadAllDataAsync(fp, selectedSheet);

                // Apply filtering and renaming if mapped
                if (config.ColumnMappingsByFile != null && config.ColumnMappingsByFile.TryGetValue(fp, out var mappings))
                {
                    var mappedData = new List<Dictionary<string, object?>>();
                    foreach (var row in fileData)
                    {
                        var newRow = new Dictionary<string, object?>();
                        foreach (var mapping in mappings)
                        {
                            if (row.TryGetValue(mapping.Key, out var val))
                            {
                                newRow[mapping.Value] = val; // Rename and keep only selected
                            }
                            else
                            {
                                newRow[mapping.Value] = null; // Ensure the column exists even if missing in this row
                            }
                        }
                        mappedData.Add(newRow);
                    }
                    fileData = mappedData;
                }

                totalInput += fileData.Count;
                for (int i = 0; i < fileData.Count; i++)
                {
                    allData.Add(new RowWithMetadata
                    {
                        Row = fileData[i],
                        SourceFile = sourceFile,
                        RowIndex = i + 2
                    });
                }
            }

            // Thu thập tất cả các key columns duy nhất
            var keyColumns = config.KeyColumnsByFile
                .SelectMany(kv => kv.Value)
                .Distinct()
                .ToList();

            List<Dictionary<string, object?>> dedupedData;
            var removedDuplicates = new List<RemovedDuplicateDto>();
            int dupCount = 0;

            if (keyColumns.Any())
            {
                // Deduplication & Merge: giữ lại dòng đầu tiên của mỗi key, đắp thêm dữ liệu từ các dòng trùng lặp
                var dedupDict = new Dictionary<string, RowWithMetadata>(StringComparer.OrdinalIgnoreCase);

                foreach (var rowMeta in allData)
                {
                    var row = rowMeta.Row;
                    var keyValue = BuildKey(row, keyColumns);
                    if (string.IsNullOrWhiteSpace(keyValue))
                    {
                        // Nếu khóa rỗng (vd: dòng tiêu đề nhóm "I", "II" không có tên), không gộp, giữ nguyên dòng này
                        keyValue = Guid.NewGuid().ToString(); 
                    }

                    if (!dedupDict.TryGetValue(keyValue, out var existingMeta))
                    {
                        dedupDict[keyValue] = new RowWithMetadata
                        {
                            Row = new Dictionary<string, object?>(row),
                            SourceFile = rowMeta.SourceFile,
                            RowIndex = rowMeta.RowIndex
                        };
                    }
                    else
                    {
                        dupCount++;
                        var existingRow = existingMeta.Row;

                        removedDuplicates.Add(new RemovedDuplicateDto
                        {
                            RemovedRow = new Dictionary<string, object?>(row),
                            KeptRow = existingRow,
                            SourceFile = rowMeta.SourceFile,
                            SourceRowIndex = rowMeta.RowIndex,
                            MatchedKey = keyValue
                        });

                        // Merge các cột còn thiếu từ dòng mới vào dòng đã tồn tại
                        foreach (var kvp in row)
                        {
                            var hasValueInExisting = existingRow.TryGetValue(kvp.Key, out var existingVal) && 
                                                     existingVal != null && 
                                                     !string.IsNullOrWhiteSpace(existingVal.ToString());
                                                     
                            var hasValueInNew = kvp.Value != null && 
                                                !string.IsNullOrWhiteSpace(kvp.Value.ToString());

                            if (!hasValueInExisting && hasValueInNew)
                            {
                                existingRow[kvp.Key] = kvp.Value;
                            }
                        }
                    }
                }
                dedupedData = dedupDict.Values.Select(v => v.Row).ToList();

                for (int i = 0; i < removedDuplicates.Count; i++)
                {
                    var keptIdx = dedupedData.IndexOf(removedDuplicates[i].KeptRow);
                    removedDuplicates[i].KeptRowIndex = keptIdx >= 0 ? keptIdx + 1 : 1;
                }
            }
            else
            {
                dedupedData = allData.Select(x => x.Row).ToList();
            }

            // Thu thập toàn bộ headers từ tất cả data rows
            var allHeaders = allData
                .SelectMany(r => r.Row.Keys)
                .Distinct()
                .ToList();

            return new MergeResultDto
            {
                Rows = dedupedData,
                RemovedDuplicates = removedDuplicates,
                Headers = allHeaders,
                TotalInput = totalInput,
                TotalOutput = dedupedData.Count,
                TotalDuplicate = dupCount
            };
        }

        /// <summary>
        /// Left Join: gắn cột từ file phụ vào file gốc theo key.
        /// Port từ logic Python: DragDropMappingScreen → handle_drag_drop_confirmed.
        /// </summary>
        public async Task<MergeResultDto> LeftJoinAsync(
            string masterFilePath,
            List<string> auxFilePaths,
            List<ColumnMappingItem> mappings,
            List<string> keyColumns,
            Dictionary<string, string>? selectedSheetByFile = null)
        {
            string? masterSheet = null;
            if (selectedSheetByFile != null && selectedSheetByFile.TryGetValue(masterFilePath, out var sMaster))
            {
                masterSheet = sMaster;
            }

            var masterData = await _excelService.ReadAllDataAsync(masterFilePath, masterSheet);

            // Tải dữ liệu các file phụ vào từ điển
            var auxDataMap = new Dictionary<string, List<Dictionary<string, object?>>>();
            foreach (var auxFp in auxFilePaths)
            {
                string? auxSheet = null;
                if (selectedSheetByFile != null && selectedSheetByFile.TryGetValue(auxFp, out var sAux))
                {
                    auxSheet = sAux;
                }
                auxDataMap[auxFp] = await _excelService.ReadAllDataAsync(auxFp, auxSheet);
            }
            
            // Index các file phụ theo key để lookup O(1)
            var auxIndexes = new Dictionary<string, Dictionary<string, Dictionary<string, object?>>>();
            foreach (var auxPath in auxFilePaths)
            {
                var auxData = auxDataMap[auxPath];
                var index = new Dictionary<string, Dictionary<string, object?>>(StringComparer.OrdinalIgnoreCase);
                foreach (var row in auxData)
                {
                    var key = BuildKey(row, keyColumns);
                    if (!string.IsNullOrEmpty(key) && !index.ContainsKey(key))
                        index[key] = row;
                }
                auxIndexes[auxPath] = index;
            }

            // Thực hiện join
            var result = new List<Dictionary<string, object?>>();
            foreach (var masterRow in masterData)
            {
                var outputRow = new Dictionary<string, object?>(masterRow);
                var masterKey = BuildKey(masterRow, keyColumns);

                foreach (var mapping in mappings)
                {
                    if (auxIndexes.TryGetValue(mapping.AuxFile, out var auxIndex) &&
                        auxIndex.TryGetValue(masterKey, out var auxRow) &&
                        auxRow.TryGetValue(mapping.AuxColumn, out var auxVal))
                    {
                        outputRow[mapping.OutputColumnName] = auxVal;
                    }
                    else
                    {
                        outputRow[mapping.OutputColumnName] = null;
                    }
                }

                result.Add(outputRow);
            }

            var allHeaders = result.SelectMany(r => r.Keys).Distinct().ToList();

            return new MergeResultDto
            {
                Rows = result,
                Headers = allHeaders,
                TotalInput = masterData.Count,
                TotalOutput = result.Count,
                TotalDuplicate = 0
            };
        }

        private static string BuildKey(Dictionary<string, object?> row, List<string> keyColumns)
        {
            return string.Join("|||", keyColumns.Select(k =>
                row.TryGetValue(k, out var v) ? (v?.ToString()?.Trim() ?? "") : ""));
        }
    }
}
