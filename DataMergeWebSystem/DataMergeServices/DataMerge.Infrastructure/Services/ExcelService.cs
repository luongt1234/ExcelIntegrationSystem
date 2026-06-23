using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;
using OfficeOpenXml;
using System.Text;
using System.Globalization;

namespace DataMerge.Infrastructure.Services
{
    public class ExcelService : IExcelService
    {
        private static readonly string[] HeaderKeywords = new[]
        {
            "stt", "ho va ten", "ho ten", "ho va ten ung vien", "ten ung vien", "hoten", "fullname", "full name",
            "ngay sinh", "nam sinh", "sinh ngay", "dob",
            "cccd", "cmnd", "can cuoc", "so dinh danh",
            "so dien thoai", "dien thoai", "sdt", "phone", "mobile", "tel",
            "email", "dia chi", "vi tri", "chuc danh", "trinh do", "ghi chu", "ket qua", "tinh trang"
        };

        public ExcelService()
        {
            // EPPlus 5+ cần khai báo license context
            ExcelPackage.LicenseContext = LicenseContext.NonCommercial;
        }

        private static string NormalizeText(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return string.Empty;
            var normalizedString = text.Normalize(NormalizationForm.FormD);
            var stringBuilder = new StringBuilder();

            foreach (var c in normalizedString)
            {
                var unicodeCategory = CharUnicodeInfo.GetUnicodeCategory(c);
                if (unicodeCategory != UnicodeCategory.NonSpacingMark)
                {
                    stringBuilder.Append(c);
                }
            }
            return stringBuilder.ToString().Normalize(NormalizationForm.FormC).ToLowerInvariant();
        }

        private string GetMergedCellValue(ExcelWorksheet ws, int row, int col)
        {
            var cell = ws.Cells[row, col];
            if (cell.Merge)
            {
                foreach (var mergedRange in ws.MergedCells)
                {
                    var range = ws.Cells[mergedRange];
                    if (row >= range.Start.Row && row <= range.End.Row &&
                        col >= range.Start.Column && col <= range.End.Column)
                    {
                        return ws.Cells[range.Start.Row, range.Start.Column].Text?.Trim() ?? "";
                    }
                }
            }
            return cell.Text?.Trim() ?? "";
        }

        private (int headerStartRow, int headerEndRow) DetectHeaderRow(ExcelWorksheet ws, out List<string> detectedHeaders)
        {
            detectedHeaders = new List<string>();
            if (ws.Dimension == null) return (1, 1);

            int maxScan = Math.Min(50, ws.Dimension.Rows);
            int bestRow = 1;

            // ƯU TIÊN 1: SĂN TÌM CỘT "STT"
            // Quét tìm ô chứa "stt", "số tt", "no" trong 5 cột đầu
            for (int r = 1; r <= maxScan; r++)
            {
                int maxColCheck = Math.Min(5, ws.Dimension.Columns);
                for (int c = 1; c <= maxColCheck; c++)
                {
                    var cellText = GetMergedCellValue(ws, r, c);
                    var norm = NormalizeText(cellText);
                    
                    if (norm == "stt" || norm == "so tt" || norm == "so thu tu" || norm == "no" || norm == "no.")
                    {
                        var sttCell = ws.Cells[r, c];
                        int headerEndRow = r;
                        bool isMerged = false;
                        if (sttCell.Merge)
                        {
                            foreach (var mergedRange in ws.MergedCells)
                            {
                                var range = ws.Cells[mergedRange];
                                if (r >= range.Start.Row && r <= range.End.Row &&
                                    c >= range.Start.Column && c <= range.End.Column)
                                {
                                    headerEndRow = range.End.Row;
                                    isMerged = true;
                                    break;
                                }
                            }
                        }

                        int dataStartRow = -1;
                        if (isMerged && headerEndRow > r)
                        {
                            // Nếu STT được Merge dọc chuẩn chỉ, boundary của nó chính xác là biên giới của Header!
                            dataStartRow = headerEndRow + 1;
                        }
                        else
                        {
                            // Nếu STT không được merge dọc (người dùng gõ text bình thường), dùng logic dò số đếm
                            for (int nextR = r + 1; nextR <= Math.Min(r + 5, ws.Dimension.Rows); nextR++)
                            {
                                var nextVal = GetMergedCellValue(ws, nextR, c);
                                if (int.TryParse(nextVal, out int num) && num > 0 && num <= 10)
                                {
                                    dataStartRow = nextR;
                                    break;
                                }
                            }
                        }

                        if (dataStartRow != -1)
                        {
                            bestRow = r;
                            for (int col = 1; col <= ws.Dimension.Columns; col++)
                            {
                                List<string> headerParts = new List<string>();
                                for (int hr = bestRow; hr < dataStartRow; hr++)
                                {
                                    var text = GetMergedCellValue(ws, hr, col);
                                    if (!string.IsNullOrEmpty(text) && (headerParts.Count == 0 || headerParts[headerParts.Count - 1] != text))
                                    {
                                        headerParts.Add(text);
                                    }
                                }
                                if (headerParts.Count == 1)
                                {
                                    detectedHeaders.Add(headerParts[0]);
                                }
                                else if (headerParts.Count > 1)
                                {
                                    detectedHeaders.Add(headerParts[0] + " - " + headerParts[headerParts.Count - 1]);
                                }
                                else
                                {
                                    detectedHeaders.Add(string.Empty);
                                }
                            }
                            return (bestRow, dataStartRow - 1); // Trả về dòng đầu và cuối của header
                        }
                    }
                }
            }

            // ƯU TIÊN 2: CHẤM ĐIỂM TỪ KHÓA (Fallback)
            // Áp dụng nếu file không có cột STT, hoặc file là template trống (không có dữ liệu số bên dưới)
            int maxScore = -1;
            for (int r = 1; r <= maxScan; r++)
            {
                int score = 0;
                var currentHeaders = new List<string>();
                for (int c = 1; c <= ws.Dimension.Columns; c++)
                {
                    var text = ws.Cells[r, c].Text?.Trim() ?? string.Empty;
                    currentHeaders.Add(text);

                    var normText = NormalizeText(text);
                    if (!string.IsNullOrEmpty(normText) && HeaderKeywords.Any(k => normText.Contains(k)))
                    {
                        score++;
                    }
                }

                if (score > maxScore)
                {
                    maxScore = score;
                    bestRow = r;
                    detectedHeaders = currentHeaders;
                }
            }

            // ƯU TIÊN 3: MẶC ĐỊNH DÒNG 1 (Fallback cuối cùng)
            if (maxScore <= 0)
            {
                bestRow = 1;
                detectedHeaders.Clear();
                for (int c = 1; c <= ws.Dimension.Columns; c++)
                {
                    detectedHeaders.Add(ws.Cells[1, c].Text?.Trim() ?? string.Empty);
                }
            }

            return (bestRow, bestRow);
        }

        private List<List<HeaderCellDto>> BuildHeaderGrid(ExcelWorksheet ws, int startRow, int endRow)
        {
            var grid = new List<List<HeaderCellDto>>();
            var skipCells = new HashSet<(int r, int c)>();
            int numCols = ws.Dimension?.Columns ?? 0;

            for (int r = startRow; r <= endRow; r++)
            {
                var rowList = new List<HeaderCellDto>();
                for (int c = 1; c <= numCols; c++)
                {
                    if (skipCells.Contains((r, c))) continue;

                    var cell = ws.Cells[r, c];
                    var dto = new HeaderCellDto 
                    { 
                        Text = cell.Text?.Trim() ?? string.Empty, 
                        RowSpan = 1, 
                        ColSpan = 1 
                    };
                    dto.CoveredColumns.Add(c - 1);

                    if (cell.Merge)
                    {
                        var mergeAddress = ws.MergedCells[r, c];
                        if (mergeAddress != null)
                        {
                            var range = ws.Cells[mergeAddress];
                            dto.RowSpan = range.End.Row - range.Start.Row + 1;
                            dto.ColSpan = range.End.Column - range.Start.Column + 1;
                            dto.Text = ws.Cells[range.Start.Row, range.Start.Column].Text?.Trim() ?? string.Empty;
                            
                            dto.CoveredColumns.Clear();
                            for (int cc = range.Start.Column; cc <= range.End.Column; cc++)
                            {
                                dto.CoveredColumns.Add(cc - 1);
                            }

                            // Add to skipCells so we don't process them again
                            for (int skipR = range.Start.Row; skipR <= range.End.Row; skipR++)
                            {
                                for (int skipC = range.Start.Column; skipC <= range.End.Column; skipC++)
                                {
                                    if (skipR == r && skipC == c) continue;
                                    skipCells.Add((skipR, skipC));
                                }
                            }
                        }
                    }
                    rowList.Add(dto);
                }
                grid.Add(rowList);
            }
            return grid;
        }

        public async Task<ExcelFileStructure> ReadStructureAsync(string filePath, string? sheetName = null)
        {
            var structure = new ExcelFileStructure
            {
                FilePath = filePath,
                FileName = Path.GetFileName(filePath)
            };

            await Task.Run(() =>
            {
                using var package = new ExcelPackage(new FileInfo(filePath));
                var ws = string.IsNullOrEmpty(sheetName) ? package.Workbook.Worksheets.FirstOrDefault() : package.Workbook.Worksheets[sheetName];
                if (ws == null || ws.Dimension == null) return;

                structure.SheetNames = package.Workbook.Worksheets.Select(x => x.Name).ToList();
                structure.SelectedSheet = ws.Name;

                var (headerStartRow, headerEndRow) = DetectHeaderRow(ws, out var rawHeaders);

                // Build header grid
                structure.HeaderGrid = BuildHeaderGrid(ws, headerStartRow, headerEndRow);

                // Đọc header đã detect
                for (int col = 1; col <= ws.Dimension.Columns; col++)
                {
                    var h = rawHeaders.ElementAtOrDefault(col - 1)?.Trim();
                    structure.Headers.Add(string.IsNullOrEmpty(h) ? $"Col{col}" : h);
                }
                // Tổng số dòng dữ liệu (trừ header và các dòng rác phía trên)
                structure.TotalRows = Math.Max(0, ws.Dimension.Rows - headerEndRow);
            });

            return structure;
        }

        public async Task<List<Dictionary<string, object?>>> ReadAllDataAsync(string filePath, string? sheetName = null)
        {
            var result = new List<Dictionary<string, object?>>();

            await Task.Run(() =>
            {
                using var package = new ExcelPackage(new FileInfo(filePath));
                var ws = string.IsNullOrEmpty(sheetName) ? package.Workbook.Worksheets.FirstOrDefault() : package.Workbook.Worksheets[sheetName];
                if (ws == null || ws.Dimension == null) return;

                var (headerStartRow, headerEndRow) = DetectHeaderRow(ws, out var rawHeaders);

                // Lấy headers
                var headers = new List<string>();
                for (int col = 1; col <= ws.Dimension.Columns; col++)
                {
                    var h = rawHeaders.ElementAtOrDefault(col - 1)?.Trim();
                    headers.Add(string.IsNullOrEmpty(h) ? $"Col{col}" : h);
                }

                // Đọc từng dòng dữ liệu từ dưới dòng header
                for (int row = headerEndRow + 1; row <= ws.Dimension.Rows; row++)
                {
                    var dict = new Dictionary<string, object?>();
                    bool hasData = false;

                    for (int col = 1; col <= headers.Count; col++)
                    {
                        var cell = ws.Cells[row, col];
                        var val = cell.Value;
                        string? strVal = null;

                        if (val is DateTime dt)
                        {
                            strVal = dt.ToString("dd/MM/yyyy");
                        }
                        else
                        {
                            strVal = val?.ToString();
                        }

                        // Nếu Value rỗng (ví dụ do là công thức chưa được tính toán), thử lấy Text hiển thị
                        if (string.IsNullOrWhiteSpace(strVal) && !string.IsNullOrWhiteSpace(cell.Text))
                        {
                            strVal = cell.Text;
                        }

                        dict[headers[col - 1]] = strVal;
                        if (!string.IsNullOrWhiteSpace(strVal)) hasData = true;
                    }

                    if (hasData) result.Add(dict);
                }
            });

            return result;
        }

        public async Task<byte[]> WriteToExcelAsync(List<Dictionary<string, object?>> data, string sheetName = "Sheet1")
        {
            return await Task.Run(() =>
            {
                using var package = new ExcelPackage();
                var ws = package.Workbook.Worksheets.Add(sheetName);

                if (!data.Any()) return package.GetAsByteArray();

                var headers = data.SelectMany(r => r.Keys).Distinct().ToList();

                // Viết header
                for (int col = 0; col < headers.Count; col++)
                {
                    ws.Cells[1, col + 1].Value = headers[col];
                    ws.Cells[1, col + 1].Style.Font.Bold = true;
                    ws.Cells[1, col + 1].Style.Fill.PatternType = OfficeOpenXml.Style.ExcelFillStyle.Solid;
                    ws.Cells[1, col + 1].Style.Fill.BackgroundColor.SetColor(System.Drawing.Color.FromArgb(0x1E, 0x3A, 0x5F));
                    ws.Cells[1, col + 1].Style.Font.Color.SetColor(System.Drawing.Color.White);
                }

                // Viết data
                for (int row = 0; row < data.Count; row++)
                {
                    for (int col = 0; col < headers.Count; col++)
                    {
                        ws.Cells[row + 2, col + 1].Value = data[row].GetValueOrDefault(headers[col]);
                    }
                }

                ws.Cells[ws.Dimension.Address].AutoFitColumns();
                return package.GetAsByteArray();
            });
        }
    }
}
