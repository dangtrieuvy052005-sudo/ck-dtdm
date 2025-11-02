# Application Backend Server
FROM python:3.11-slim
WORKDIR /app
COPY . .

# Chỉ cài các thư viện cần thiết cho dịch vụ Flask
RUN pip install --no-cache-dir "flask>=2.3,<3.0" "requests>=2.31" "pyjwt[crypto]>=2.8"

EXPOSE 8081
CMD ["python", "app.py"]
