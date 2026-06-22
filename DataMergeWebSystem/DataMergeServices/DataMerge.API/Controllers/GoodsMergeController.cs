using DataMerge.Application.Interfaces;
using DataMerge.Domain.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace DataMerge.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class GoodsMergeController : ControllerBase
    {
        private readonly IGoodsMatcherService _goodsMatcher;
        private readonly IFileUploadService _uploadService;

        public GoodsMergeController(IGoodsMatcherService goodsMatcher, IFileUploadService uploadService)
        {
            _goodsMatcher = goodsMatcher;
            _uploadService = uploadService;
        }

        /// <summary>So khớp file Input với Catalog, trả về kết quả phân loại 3 nhóm.</summary>
        [HttpPost("match")]
        public async Task<IActionResult> Match([FromBody] GoodsMatchRequest request)
        {
            var inputPath = _uploadService.GetTempFilePath(request.InputFileId);
            var catalogPath = _uploadService.GetTempFilePath(request.CatalogFileId);

            if (!System.IO.File.Exists(inputPath))
                return NotFound("File Input không tồn tại.");
            if (!System.IO.File.Exists(catalogPath))
                return NotFound("File Catalog không tồn tại.");

            var result = await _goodsMatcher.MatchAsync(inputPath, catalogPath, request.MatchColumn);
            return Ok(result);
        }

        /// <summary>Cập nhật trạng thái một dòng (Approve/Reject/Restore).</summary>
        [HttpPost("update-status")]
        public IActionResult UpdateStatus([FromBody] UpdateStatusRequest request)
        {
            // Logic này sẽ được frontend quản lý state-side, BE chỉ cần hỗ trợ
            // export cuối cùng. Endpoint này phục vụ cho trường hợp muốn persist.
            return Ok(new { message = "Đã cập nhật trạng thái." });
        }

        /// <summary>Xuất danh sách Approved ra file Excel.</summary>
        [HttpPost("export")]
        public async Task<IActionResult> Export([FromBody] GoodsMatchResult result)
        {
            var bytes = await _goodsMatcher.ExportApprovedAsync(result);
            return File(bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "KetQua_HangHoa.xlsx");
        }
    }

    public class GoodsMatchRequest
    {
        public string InputFileId { get; set; } = string.Empty;
        public string CatalogFileId { get; set; } = string.Empty;
        public string MatchColumn { get; set; } = string.Empty;
    }

    public class UpdateStatusRequest
    {
        public int RowIndex { get; set; }
        public string NewStatus { get; set; } = string.Empty;
    }
}
