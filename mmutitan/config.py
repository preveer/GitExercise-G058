import os

class Config:
    # This is the "Secret Key" that Flask needs for security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mmu_titan_secret_key_123'
    
    # This tells Flask where your database file is located
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mmutitan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False