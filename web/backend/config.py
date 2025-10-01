import os


class AppConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # MySQL connection (adjust to your environment)
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DB = os.getenv("MYSQL_DB", "jp_site")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    # CORS
    CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")

    # Admin
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-admin-key")

    # External services
    MERCARI_BASE = os.getenv("MERCARI_BASE", "https://jp.mercari.com") 