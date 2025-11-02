-- Khởi tạo cơ sở dữ liệu cho hệ thống MiniCloud
-- Tạo database studentdb và bảng students với dữ liệu mẫu

CREATE DATABASE IF NOT EXISTS studentdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE studentdb;

CREATE TABLE IF NOT EXISTS students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_code VARCHAR(20) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  major VARCHAR(100) NOT NULL,
  gpa DECIMAL(3,2) NOT NULL CHECK (gpa BETWEEN 0 AND 4),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO students (student_code, full_name, major, gpa) VALUES
  ('SV001', 'Nguyễn Văn A', 'Công nghệ thông tin', 3.20),
  ('SV002', 'Trần Thị B', 'Kỹ thuật phần mềm', 3.50),
  ('SV003', 'Lê Văn C', 'Hệ thống thông tin', 3.10)
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  major = VALUES(major),
  gpa = VALUES(gpa);
