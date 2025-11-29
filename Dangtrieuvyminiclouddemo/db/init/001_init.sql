-- Khởi tạo cơ sở dữ liệu cho hệ thống MiniCloud
-- Tạo database studentdb và bảng students với dữ liệu mẫu đúng yêu cầu đề bài

CREATE DATABASE IF NOT EXISTS studentdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE studentdb;

CREATE TABLE IF NOT EXISTS students (
  student_id VARCHAR(20) PRIMARY KEY,
  fullname VARCHAR(100) NOT NULL,
  dob DATE NOT NULL,
  major VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO students (student_id, fullname, dob, major) VALUES
  ('SV001', 'Nguyễn Văn A', '2001-03-15', 'Công nghệ thông tin'),
  ('SV002', 'Trần Thị B', '2001-07-21', 'Kỹ thuật phần mềm'),
  ('SV003', 'Lê Văn C', '2002-01-09', 'Hệ thống thông tin')
ON DUPLICATE KEY UPDATE
  fullname = VALUES(fullname),
  dob = VALUES(dob),
  major = VALUES(major);
