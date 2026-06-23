import os


class Config:
    # Secret key for session security and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mmu_titan_secret_key_123'


    # SQLite database file location
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mmutitan.db'


    # Disable modification tracking (saves memory, not needed)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
