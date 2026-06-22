using System;

namespace DataMerge.Domain.Entities
{
    public class User
    {
        public int Id { get; set; }
        public string Username { get; set; } = string.Empty;
        public string PasswordHash { get; set; } = string.Empty;
        public string Role { get; set; } = "User"; // Đơn giản hóa role
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}
