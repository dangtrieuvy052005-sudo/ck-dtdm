# 2. Application Backend Server
FROM python:3.11-slim
WORKDIR /app
COPY . .

# CẬP NHẬT: Thêm 'requests' và 'python-jose'
# 'requests' dùng để gọi Keycloak (ở hàm get_public_key)
# 'python-jose' dùng để giải mã JWT (ở API /secure)
RUN pip install flask requests python-jose

EXPOSE 8081
# File app.py của Cấp độ 2 chạy ở cổng 8081
CMD ["python", "app.py"]

