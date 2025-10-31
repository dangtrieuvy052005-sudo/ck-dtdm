# 2. Application Backend Server (Flask)
# File /app/app.py
# ĐÃ CẬP NHẬT (Yêu cầu mở rộng #2)

from flask import Flask, jsonify, request
import time, requests, os
from jose import jwt
import json # <-- THÊM MỚI

# Lấy thông tin từ biến môi trường (đặt trong docker-compose.yml)
KEYCLOAK_SERVER = os.environ.get('KEYCLOAK_SERVER', 'http://auth:8080')
KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM', 'MiniCloudRealm')

# URL của Keycloak để lấy public key
KEYCLOAK_CERTS_URL = f"{KEYCLOAK_SERVER}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"

app = Flask(__name__)

# Cache để lưu public key, tránh gọi Keycloak liên tục
public_key_cache = None
cache_time = 0
CACHE_TTL = 3600 # Cache trong 1 giờ

def get_public_key():
    """
    Lấy public key từ Keycloak (có cache).
    """
    global public_key_cache, cache_time
    now = time.time()

    # Nếu cache còn hạn, dùng cache
    if public_key_cache and (now - cache_time < CACHE_TTL):
        return public_key_cache
    
    # Nếu cache hết hạn, gọi Keycloak
    try:
        response = requests.get(KEYCLOAK_CERTS_URL)
        response.raise_for_status() # Báo lỗi nếu request thất bại
        
        jwks = response.json()
        
        # Thường chỉ có 1 key, nhưng ta nên lặp qua
        for key in jwks['keys']:
            if key['use'] == 'sig': # Key dùng để ký (signature)
                # Keycloak cung cấp nhiều thông tin, ta chỉ cần 1 public key
                # Đây là cách chuẩn để build 1 key PEM từ thông tin JWKS
                public_key_cache = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                cache_time = now
                return public_key_cache
        
        raise Exception("Không tìm thấy public key (sig) trong JWKS.")

    except Exception as e:
        print(f"Lỗi khi lấy public key: {e}")
        return None

# --- API CƠ BẢN ---
@app.get("/hello")
def hello(): 
    return jsonify(message="Hello from App Server!")

# --- BẮT ĐẦU CODE MỚI (Yêu cầu mở rộng #2) ---
# API /student đọc từ file JSON
@app.get("/student")
def student(): 
    try:
        # 'encoding="utf-8"' để đọc tiếng Việt
        with open("students.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify(error="students.json not found"), 404
    except Exception as e:
        return jsonify(error=str(e)), 500
# --- KẾT THÚC CODE MỚI ---

# --- API BẢO MẬT (Dùng cho Cấp độ 2) ---
@app.get("/secure")
def secure_api():
    # 1. Lấy token từ Header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify(error="Thiếu Authorization Header"), 401

    try:
        # Tách "Bearer <token>"
        token_type, token = auth_header.split()
        if token_type.lower() != 'bearer':
            raise ValueError("Token type phải là Bearer")

    except ValueError as e:
        return jsonify(error=f"Sai định dạng token: {e}"), 401
    
    # 2. Lấy public key
    public_key = get_public_key()
    if not public_key:
        return jsonify(error="Không thể lấy public key từ Keycloak"), 500
    
    # 3. Giải mã và xác thực token
    try:
        # 'audience' là 'account' (client-id mặc định của Keycloak)
        # Bạn có thể đổi 'audience' nếu client của bạn có tên khác
        payload = jwt.decode(token, public_key, algorithms=['RS256'], audience='account') 
        
        # 4. Thành công
        username = payload.get('preferred_username', 'Không rõ')
        return jsonify(
            message=f"Xin chào {username}! Đây là API BẢO MẬT.",
            token_payload=payload
        )

    except jwt.ExpiredSignatureError:
        return jsonify(error="Token đã hết hạn"), 401
    except jwt.JWTClaimsError as e:
        return jsonify(error=f"Token claim không hợp lệ (ví dụ: sai audience): {e}"), 401
    except Exception as e:
        return jsonify(error=f"Token không hợp lệ: {e}"), 401

# --- Chạy server ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081, debug=True)

