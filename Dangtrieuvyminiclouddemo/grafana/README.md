# Grafana provisioning và hướng dẫn demo

Cấu hình trong thư mục này giúp Grafana tự động:

- Đăng ký datasource **Prometheus** (trỏ đến `monitor:9090`).
- Nạp provider "System Health" và dashboard mẫu `MiniCloud System Health` từ thư mục `dashboards/`.

## Nếu cần thay đổi tổ chức/folder

Trong trường hợp bạn đổi `orgId` hoặc muốn đặt dashboard vào folder khác:
1. Cập nhật `grafana/provisioning/dashboards/dashboard.yml` với `orgId` hoặc `folder` mong muốn.
2. Nếu đổi tên datasource, chỉnh sửa `grafana/provisioning/datasources/datasource.yml` và phần `datasource` trong `dashboards/system-health.json` cho trùng khớp.
3. Khởi động lại container Grafana: `docker compose restart grafana`.
4. Đăng nhập Grafana (mặc định `admin/admin`), vào **Dashboards → Browse** để kiểm tra dashboard đã nằm đúng folder mới.

## Demo nhanh khi chấm điểm

1. Chạy `docker compose up monitor grafana proxy app web web2` để có dữ liệu Prometheus và HTTP request.
2. Truy cập `http://localhost:3000`, đăng nhập và mở dashboard **MiniCloud System Health**.
3. Gửi vài request tới `http://localhost:8085/hello` hoặc qua proxy `http://localhost:8088/api/hello` để đồ thị HTTP Requests/Endpoints hiển thị số liệu.
4. Dữ liệu CPU/RAM lấy từ Node Exporter; số sinh viên từ metric `app_students_total` của backend.
