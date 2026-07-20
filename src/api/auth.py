# src/api/auth.py
import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    # Read allowed credentials from environment (defaults to admin/admin if not set for safety during dev)
    expected_username = os.getenv("WEB_USER", "admin").encode("utf8")
    expected_password = os.getenv("WEB_PASSWORD", "admin").encode("utf8")

    current_username_bytes = credentials.username.encode("utf8")
    current_password_bytes = credentials.password.encode("utf8")

    # Use secrets.compare_digest to prevent timing attacks
    is_correct_username = secrets.compare_digest(current_username_bytes, expected_username)
    is_correct_password = secrets.compare_digest(current_password_bytes, expected_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.username
