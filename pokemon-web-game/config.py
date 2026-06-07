# Database Configuration
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# MariaDB 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'pokemon_db'),
    'charset': 'utf8mb4',
    'cursorclass': 'DictCursor'  # PyMySQL에서 딕셔너리로 결과 반환
}

# Flask 설정
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))