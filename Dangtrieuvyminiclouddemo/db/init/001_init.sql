-- 3. Relational Database Server (MariaDB)
-- File SQL này sẽ tự động chạy khi container MariaDB khởi động lần đầu tiên

-- Tạo database nếu chưa tồn tại
CREATE DATABASE IF NOT EXISTS minicloud;

-- Sử dụng database
USE minicloud;

-- Tạo bảng 'notes' nếu chưa tồn tại
CREATE TABLE IF NOT EXISTS notes(
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chèn dữ liệu mẫu
INSERT INTO notes(title) VALUES ('Hello from MariaDB!');
