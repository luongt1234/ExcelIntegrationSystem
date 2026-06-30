using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace DataMerge.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class DynamicPivotController : ControllerBase
    {
        private readonly IDynamicPivotService _pivotService;
        private readonly IFileUploadService _uploadService;

        public DynamicPivotController(IDynamicPivotService pivotService, IFileUploadService uploadService)
        {
            _pivotService = pivotService;
            _uploadService = uploadService;
        }

        [HttpPost("analyze")]
        public async Task<IActionResult> Analyze([FromBody] PivotAnalyzeRequest request)
        {
            var filePath = _uploadService.GetTempFilePath(request.FileId);
            if (!System.IO.File.Exists(filePath))
                return NotFound("File không tồn tại hoặc đã hết hạn.");

            var result = await _pivotService.AnalyzeAsync(filePath, request);
            return Ok(result);
        }

        [HttpPost("preview")]
        public async Task<IActionResult> Preview([FromBody] PivotExecuteConfig config)
        {
            var filePath = _uploadService.GetTempFilePath(config.FileId);
            if (!System.IO.File.Exists(filePath))
                return NotFound("File không tồn tại hoặc đã hết hạn.");

            var result = await _pivotService.PreviewAsync(filePath, config);
            return Ok(result);
        }

        [HttpPost("export")]
        public async Task<IActionResult> Export([FromBody] PivotExecuteConfig config)
        {
            var filePath = _uploadService.GetTempFilePath(config.FileId);
            if (!System.IO.File.Exists(filePath))
                return NotFound("File không tồn tại hoặc đã hết hạn.");

            var bytes = await _pivotService.ExportAsync(filePath, config);
            return File(bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "KetQua_ChuyenDoiDocNgang.xlsx");
        }
    }
}
