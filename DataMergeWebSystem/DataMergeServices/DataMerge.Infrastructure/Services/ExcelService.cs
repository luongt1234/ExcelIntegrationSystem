using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;
using OfficeOpenXml;

namespace DataMerge.Infrastructure.Services
{
    public class ExcelService : IExcelService
    {
        public ExcelService()
        {
            // EPPlus 5+ cần khai báo license context
            ExcelPackage.LicenseContext = LicenseContext.NonCommercial;
        }

        public async Task<ExcelFileStructure> ReadStructureAsync(string filePath)
        {
            var structure = new ExcelFileStructure
            {
                FilePath = filePath,
                FileName = Path.GetFileName(filePath)
            };

            await Task.Run(() =>
            {
                using var package = new ExcelPackage(new FileInfo(filePath));
                var ws = package.Workbook.Worksheets.FirstOrDefault();
                if (ws == null) return;

                // Đọc header hàng 1
                for (int col = 1; col <= ws.Dimension.Columns; col++)
                {
                    var header = ws.Cells[1, col].Text?.Trim();
                    if (!string.IsNullOrEmpty(header))
                        structure.Headers.Add(header);
                }
                // Tổng số dòng dữ liệu (trừ header)
                structure.TotalRows = Math.Max(0, ws.Dimension.Rows - 1);
            });

            return structure;
        }

        public async Task<List<Dictionary<string, object?>>> ReadAllDataAsync(string filePath)
        {
            var result = new List<Dictionary<string, object?>>();

            await Task.Run(() =>
            {
                using var package = new ExcelPackage(new FileInfo(filePath));
                var ws = package.Workbook.Worksheets.FirstOrDefault();
                if (ws == null || ws.Dimension == null) return;

                // Lấy headers từ hàng 1
                var headers = new List<string>();
                for (int col = 1; col <= ws.Dimension.Columns; col++)
                {
                    var h = ws.Cells[1, col].Text?.Trim() ?? $"Col{col}";
                    headers.Add(string.IsNullOrEmpty(h) ? $"Col{col}" : h);
                }

                // Đọc từng dòng dữ liệu
                for (int row = 2; row <= ws.Dimension.Rows; row++)
                {
                    var dict = new Dictionary<string, object?>();
                    bool hasData = false;

                    for (int col = 1; col <= headers.Count; col++)
                    {
                        var cell = ws.Cells[row, col];
                        var val = cell.Value;
                        dict[headers[col - 1]] = val;
                        if (val != null) hasData = true;
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

                var headers = data.First().Keys.ToList();

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
