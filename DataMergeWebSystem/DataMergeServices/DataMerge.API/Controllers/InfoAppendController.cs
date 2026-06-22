using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace DataMerge.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class InfoAppendController : ControllerBase
    {
        private readonly IMergeService _mergeService;
        private readonly IFileUploadService _uploadService;
        private readonly IExcelService _excelService;

        public InfoAppendController(
            IMergeService mergeService,
            IFileUploadService uploadService,
            IExcelService excelService)
        {
            _mergeService = mergeService;
            _uploadService = uploadService;
            _excelService = excelService;
        }

        /// <summary>Thực hiện Left Join: đắp cột từ file phụ vào file gốc.</summary>
        [HttpPost("join")]
        public async Task<IActionResult> LeftJoin([FromBody] LeftJoinApiRequest request)
        {
            var masterPath = _uploadService.GetTempFilePath(request.MasterFileId);
            if (!System.IO.File.Exists(masterPath))
                return NotFound("File gốc không tồn tại.");

            var auxPaths = request.AuxFileIds
                .Select(id => (id, path: _uploadService.GetTempFilePath(id)))
                .ToList();

            var missing = auxPaths.Where(x => !System.IO.File.Exists(x.path)).ToList();
            if (missing.Any())
                return NotFound($"{missing.Count} file phụ không tồn tại.");

            // Map fileId → full path trong Mappings
            var mappings = request.Mappings.Select(m => new ColumnMappingItem
            {
                MasterColumn = m.MasterColumn,
                AuxFile = _uploadService.GetTempFilePath(m.AuxFileId),
                AuxColumn = m.AuxColumn,
                OutputColumnName = m.OutputColumnName
            }).ToList();

            var result = await _mergeService.LeftJoinAsync(
                masterPath,
                auxPaths.Select(x => x.path).ToList(),
                mappings,
                request.KeyColumns);

            return Ok(result);
        }

        /// <summary>Xuất kết quả Left Join ra Excel.</summary>
        [HttpPost("export")]
        public async Task<IActionResult> Export([FromBody] ExportRequest request)
        {
            var bytes = await _excelService.WriteToExcelAsync(request.Rows, "KetQua");
            return File(bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "KetQua_BoSung.xlsx");
        }
    }

    public class LeftJoinApiRequest
    {
        public string MasterFileId { get; set; } = string.Empty;
        public List<string> AuxFileIds { get; set; } = new();
        public List<ColumnMappingApiItem> Mappings { get; set; } = new();
        public List<string> KeyColumns { get; set; } = new();
    }

    public class ColumnMappingApiItem
    {
        public string MasterColumn { get; set; } = string.Empty;
        public string AuxFileId { get; set; } = string.Empty;
        public string AuxColumn { get; set; } = string.Empty;
        public string OutputColumnName { get; set; } = string.Empty;
    }
}
