import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    _db = os.getenv("DATABASE_URL", "sqlite:///../database/laboratorio.db")
    if _db.startswith("sqlite:///"):
        db_path = (_db.replace("sqlite:///", ""))
        if not Path(db_path).is_absolute():
            db_path = str((Path(__file__).resolve().parent / db_path).resolve())
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    else:
        SQLALCHEMY_DATABASE_URI = _db

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7")))
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False

    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))
    AES_SECRET_KEY = os.getenv("AES_SECRET_KEY", "change-me-32-byte-aes-key!!")[:32].ljust(32, "0")

    DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    SYSTEM_NAME = os.getenv("SYSTEM_NAME", "Sistema de Gestión Académica")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@institucion.edu")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123!")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

    TEMPLATE_FOLDER = str(ROOT / "frontend" / "templates")
    STATIC_FOLDER = str(ROOT / "frontend" / "static")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    JWT_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
