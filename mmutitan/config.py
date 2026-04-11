import os

class Config:
    SECRET_KEY = 'mmutitan-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mmutitan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'