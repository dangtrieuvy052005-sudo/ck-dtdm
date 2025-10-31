# 1. Web Frontend Server (Nginx)
# Dockerfile này xây dựng image cho web server

# Sử dụng image Nginx ổn định làm base
FROM nginx:stable

# Xóa file cấu hình default của Nginx
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy file cấu hình tùy chỉnh của chúng ta vào
COPY conf.default /etc/nginx/conf.d/default.conf

# Copy nội dung web (HTML) vào thư mục phục vụ của Nginx
COPY html/ /usr/share/nginx/html/

# Cấp quyền đọc cho các file HTML
RUN chmod -R 755 /usr/share/nginx/html

# Mở cổng 80 (cổng web mặc định)
EXPOSE 80

# Lệnh để khởi chạy Nginx khi container chạy
CMD ["nginx", "-g", "daemon off;"]
