"""
User Authentication Router
Handles user signup and login
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import secrets

from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.database.postgis import db

router = APIRouter(prefix="/api/user-auth", tags=["User Authentication"])


class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: Optional[str] = None


@router.post("/signup", response_model=UserTokenResponse)
async def user_signup(request: UserSignupRequest):
    """Register a new user"""
    
    try:
        # Check if email already exists
        existing_user = get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate unique user ID
        user_id = f"USER-{secrets.token_hex(4).upper()}"
        
        # Hash password
        password_hash = hash_password(request.password)
        
        # Create user
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, email, password_hash, full_name, phone)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, user_id, email, full_name
                """, (user_id, request.email, password_hash, request.full_name, request.phone))
                
                result = cur.fetchone()
                conn.commit()
        
        # Create JWT token
        token_data = {
            "sub": result[1],  # user_id
            "email": result[2],
            "type": "user"
        }
        access_token = create_access_token(token_data)
        
        return UserTokenResponse(
            access_token=access_token,
            user_id=result[1],
            email=result[2],
            full_name=result[3]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


@router.post("/login", response_model=UserTokenResponse)
async def user_login(request: UserLoginRequest):
    """Login user"""
    
    try:
        # Get user by email
        user = get_user_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (user['id'],))
                conn.commit()
        
        # Create JWT token
        token_data = {
            "sub": user['user_id'],
            "email": user['email'],
            "type": "user"
        }
        access_token = create_access_token(token_data)
        
        return UserTokenResponse(
            access_token=access_token,
            user_id=user['user_id'],
            email=user['email'],
            full_name=user['full_name']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


def get_user_by_email(email: str):
    """Get user by email"""
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, user_id, email, password_hash, full_name, phone
                    FROM users 
                    WHERE email = %s
                """, (email,))
                
                result = cur.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'user_id': result[1],
                        'email': result[2],
                        'password_hash': result[3],
                        'full_name': result[4],
                        'phone': result[5]
                    }
                return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None