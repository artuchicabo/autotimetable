import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "DEV_SECRET")
TOKEN_EXPIRE_HOURS = 8

def generate_token(user_id, role="teacher"):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_user(teacher_id, password):
    """Login using Teacher model from data_loader"""
    from data_loader import load_teachers
    
    teachers = load_teachers()
    
    if teacher_id not in teachers:
        return None, "USER_NOT_FOUND"
    
    teacher = teachers[teacher_id]
    
    if str(teacher.password) != str(password):
        return None, "WRONG_PASSWORD"
    
    token = generate_token(teacher.teacher_id, teacher.role)
    return token, "SUCCESS"

def require_auth(role_required=None):
    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            token = None
            if "Authorization" in request.headers:
                bearer = request.headers["Authorization"]
                token = bearer.replace("Bearer ", "")

            if not token:
                return jsonify({"error": "Missing Token"}), 401

            payload = verify_token(token)
            if payload is None:
                return jsonify({"error": "Invalid or Expired Token"}), 401

            if role_required and payload.get("role") != role_required:
                return jsonify({"error": "FORBIDDEN"}), 403

            request.user = payload
            return func(*args, **kwargs)
        return decorated
    return wrapper
