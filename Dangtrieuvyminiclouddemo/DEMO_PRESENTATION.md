# Kịch bản demo 20 phút cho dự án MyMiniCloud

Tài liệu này mô tả tuần tự các bước trình bày trong ~20 phút, kèm lệnh minh họa để chứng minh các yêu cầu của đề.

## 0'–2': Mở đầu & kiến trúc
- Giới thiệu 10 dịch vụ chính (web/web2, app, db, auth, storage, storage-init, dns, node-exporter, monitor, grafana, proxy) được khai báo trong `docker-compose.yml` và mạng `cloud-net` dùng chung. Nhấn mạnh proxy ánh xạ cổng máy chủ 8088 tránh xung đột. 
- Trình chiếu sơ đồ request: người dùng → proxy (8088) → web/web2 hoặc app (8081) → db/Keycloak/MinIO.

## 2'–5': Chuẩn bị & build image
```bash
docker compose build web web2 app
```
- Giải thích: web/web2 cùng build từ thư mục `web`, app build từ `app`. Các dịch vụ còn lại dùng image chính thức.

## 5'–7': Khởi động nền tảng
```bash
docker compose up -d db auth storage storage-init dns node-exporter monitor grafana proxy web web2 app
```
- `storage-init` sẽ tự tạo bucket `profile-pics` và `documents` khi MinIO sẵn sàng.
- Kiểm tra trạng thái:
```bash
docker compose ps
```

## 7'–11': Kiểm thử nhanh backend qua cổng nội bộ và proxy
- Truy cập trực tiếp app:
```bash
curl http://localhost:8085/hello
curl http://localhost:8085/student
```
- Đi qua proxy cân bằng tải (cổng 8088):
```bash
curl http://localhost:8088/api/hello
curl http://localhost:8088/student
```
- Minh họa `/secure`: đăng nhập Keycloak tại `http://localhost:8081`, realm `realm_sv001`, client `flask-app`; lấy token rồi gửi kèm header `Authorization: Bearer <token>` đến `http://localhost:8085/secure`.

## 11'–14': Chứng minh cơ sở dữ liệu & DNS
```bash
docker compose exec db mysql -uroot -proot -e "USE studentdb; DESCRIBE students; SELECT * FROM students;"
dig @127.0.0.1 -p 1053 app-backend.cloud.local
```
- Trình bày schema `student_id/fullname/dob/major` và bản ghi DNS (app-backend, minio, keycloak, web-frontend-server).

## 14'–16': Kiểm tra MinIO và bucket
- Mở console `http://localhost:9001` đăng nhập `minioadmin/minioadmin` để thấy hai bucket đã được tạo.
- Hoặc dùng mc (nếu có sẵn) trong container `storage-init` để liệt kê:
```bash
docker compose run --rm storage-init mc ls minio
```

## 16'–18': Prometheus & Grafana
- Prometheus: vào `http://localhost:9090/targets` xem job `backend_api`, `web`, `node-exporter` ở trạng thái `UP`.
- Grafana: `http://localhost:3000` (admin/admin). Dashboard **MiniCloud System Health** đã được provision sẵn; gửi vài request `/hello` để thấy các panel HTTP request cập nhật.

## 18'–20': Cân bằng tải & tổng kết
- Chứng minh round-robin web server bằng log:
```bash
docker compose logs -f web web2 | grep -i "GET / "
```
- Nêu lại: proxy cổng 8088, hai web, backend 8085/8081, Keycloak realm `realm_sv001`/client `flask-app`, bucket MinIO, DNS nội bộ, monitoring + dashboard.
- Trả lời Q&A.
