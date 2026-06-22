using DataMerge.Application.Interfaces;
using Microsoft.Extensions.Configuration;

namespace DataMerge.Infrastructure.Services
{
    public class FileUploadService : IFileUploadService
    {
        private readonly string _tempDir;

        public FileUploadService(IConfiguration configuration)
        {
            // Dùng thư mục được cấu hình hoặc mặc định trong thư mục hiện hành
            _tempDir = configuration["TempUploadPath"]
                ?? Path.Combine(AppContext.BaseDirectory, "TempUploads");

            if (!Directory.Exists(_tempDir))
                Directory.CreateDirectory(_tempDir);
        }

        public async Task<string> SaveTempFileAsync(Stream fileStream, string fileName)
        {
            var fileId = Guid.NewGuid().ToString("N");
            var ext = Path.GetExtension(fileName);
            var savePath = Path.Combine(_tempDir, $"{fileId}{ext}");

            using var fs = new FileStream(savePath, FileMode.Create);
            await fileStream.CopyToAsync(fs);

            return fileId + ext;
        }

        public string GetTempFilePath(string fileId)
        {
            return Path.Combine(_tempDir, fileId);
        }

        public void CleanupTempFile(string fileId)
        {
            var path = GetTempFilePath(fileId);
            if (File.Exists(path))
                File.Delete(path);
        }
    }
}
