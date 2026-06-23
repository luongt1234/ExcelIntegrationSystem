using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace DataMerge.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class PeopleMergeController : ControllerBase
    {
        private readonly IMergeService _mergeService;
        private readonly IFileUploadService _uploadService;
        private readonly IExcelService _excelService;

        public PeopleMergeController(
            IMergeService mergeService,
            IFileUploadService uploadService,
            IExcelService excelService)
        {
            _mergeService = mergeService;
            _uploadService = uploadService;
            _excelService = excelService;
        }

        /// <summary>
        /// Thực hiện Gộp & Dedup nhiều file Excel.
        /// Nhận vào danh sách fileId và cấu hình khóa gộp.
        /// </summary>
        [HttpPost("merge")]
        public async Task<IActionResult> MergeFiles([FromBody] MergeRequest request)
        {
            if (request.FileIds == null || !request.FileIds.Any())
                return BadRequest("Cần ít nhất 1 file để gộp.");

            var filePaths = request.FileIds
                .Select(id => _uploadService.GetTempFilePath(id))
                .ToList();

            var missing = filePaths.Where(p => !System.IO.File.Exists(p)).ToList();
            if (missing.Any())
                return NotFound($"Không tìm thấy {missing.Count} file. Vui lòng upload lại.");

            var mappingsByFilePath = request.ColumnMappingsByFile != null
                ? request.FileIds
                    .Where(id => request.ColumnMappingsByFile.ContainsKey(id))
                    .ToDictionary(
                        id => _uploadService.GetTempFilePath(id),
                        id => request.ColumnMappingsByFile[id]
                    )
                : null;

            var config = new MergeKeyConfig
            {
                KeyColumnsByFile = request.KeyColumnsByFile ?? request.FileIds.ToDictionary(id => id, id => new List<string>()),
                MergeMode = request.MergeMode,
                ColumnMappingsByFile = mappingsByFilePath,
                SelectedSheetByFile = request.SelectedSheetByFile
            };

            var result = await _mergeService.MergeFilesAsync(filePaths, config);
            return Ok(result);
        }

        /// <summary>Xuất kết quả merge ra file Excel để download.</summary>
        [HttpPost("export")]
        public async Task<IActionResult> ExportMergeResult([FromBody] ExportRequest request)
        {
            var bytes = await _excelService.WriteToExcelAsync(request.Rows, "KetQua");
            return File(bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "KetQua_GopHoSo.xlsx");
        }
    }

    public class MergeRequest
    {
        public List<string> FileIds { get; set; } = new();
        public Dictionary<string, List<string>>? KeyColumnsByFile { get; set; }
        public int MergeMode { get; set; } = 1;
        public Dictionary<string, Dictionary<string, string>>? ColumnMappingsByFile { get; set; }
        public Dictionary<string, string>? SelectedSheetByFile { get; set; }
    }

    public class ExportRequest
    {
        public List<Dictionary<string, object?>> Rows { get; set; } = new();
    }
}
