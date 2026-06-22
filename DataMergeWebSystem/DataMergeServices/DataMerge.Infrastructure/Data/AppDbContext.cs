using DataMerge.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace DataMerge.Infrastructure.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
        {
        }

        public DbSet<User> Users { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Data Seeding
            modelBuilder.Entity<User>().HasData(new User
            {
                Id = 1,
                Username = "admin",
                // Password = "admin", hashed using BCrypt.Net-Next hay Hash tuong tu.
                // Tam thoi de hash cua chuoi "admin" hoac pass plaintext de test neu chua cai thu vien
                PasswordHash = "$2a$11$9/Xo2.q2T9b0K4.mI1WpjeZ2D/jI.B6R3mB6P2C4J8K1Tz2M5/wF2", // Hash cua "admin"
                Role = "Admin",
                CreatedAt = new DateTime(2026, 1, 1, 0, 0, 0, DateTimeKind.Utc)
            });
        }
    }
}
