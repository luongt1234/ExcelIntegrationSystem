using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace DataMerge.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class ExcelController : ControllerBase
    {
        private readonly IFileUploadService _uploadService;
        private readonly IExcelService _excelService;

        public ExcelController(IFileUploadService uploadService, IExcelService excelService)
        {
            _uploadService = uploadService;
            _excelService = excelService;
        }

        /// <summary>Upload file Excel, trả về fileId tạm + cấu trúc header.</summary>
        [HttpPost("upload")]
        public async Task<IActionResult> Upload(IFormFile file)
        {
            if (file == null || file.Length == 0)
                return BadRequest("Không tìm thấy file.");
            if (!file.FileName.EndsWith(".xlsx") && !file.FileName.EndsWith(".xls"))
                return BadRequest("Chỉ chấp nhận file Excel (.xlsx, .xls).");

            var fileId = await _uploadService.SaveTempFileAsync(file.OpenReadStream(), file.FileName);
            var filePath = _uploadService.GetTempFilePath(fileId);
            var structure = await _excelService.ReadStructureAsync(filePath);
            structure.FilePath = fileId; // Trả fileId thay vì đường dẫn thực

            return Ok(structure);
        }

        /// <summary>Đọc toàn bộ dữ liệu của một file đã upload (dùng để preview).</summary>
        [HttpGet("{fileId}/data")]
        public async Task<IActionResult> GetData(string fileId)
        {
            var filePath = _uploadService.GetTempFilePath(fileId);
            if (!System.IO.File.Exists(filePath))
                return NotFound("File không tồn tại hoặc đã hết hạn.");

            var data = await _excelService.ReadAllDataAsync(filePath);
            return Ok(data);
        }
    }
}
