import os

class Config:
    # Secret Key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mmu_titan_secret_key_123'
    
    # Database location
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mmutitan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False