from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"

if __name__ == '__main__':
    # Lấy cổng từ biến môi trường PORT hoặc mặc định là 5000
    port = int(os.getenv("PORT", 5000))
    # Lắng nghe trên tất cả các địa chỉ IP
    app.run(host='0.0.0.0', port=port)
