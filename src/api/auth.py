"""
Authentication API endpoints.
SCRUM-11: Implement JWT authentication with refresh tokens
SCRUM-12: Add social login with Google and Apple
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from ..core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    create_refresh_token,
    decode_token
)
from ..services.user_service import UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class GoogleLoginRequest(BaseModel):
    """SCRUM-12: Google OAuth login"""
    id_token: str


class AppleLoginRequest(BaseModel):
    """SCRUM-12: Apple Sign In"""
    id_token: str
    user_info: dict = None  # First login only


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, user_service: UserService = Depends()):
    """
    Authenticate user with email/password.
    SCRUM-11: Returns access and refresh tokens.
    """
    user = await user_service.authenticate(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store refresh token in Redis for rotation - SCRUM-11
    await user_service.store_refresh_token(user.id, refresh_token)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900  # 15 minutes
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshRequest, user_service: UserService = Depends()):
    """
    Refresh an expired access token.
    SCRUM-11: Implements token rotation for security.
    """
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    
    # Verify refresh token is still valid in Redis - SCRUM-11
    is_valid = await user_service.verify_refresh_token(user_id, request.refresh_token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    # Create new token pair and rotate refresh token
    new_access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Invalidate old refresh token and store new one - SCRUM-11
    await user_service.rotate_refresh_token(user_id, request.refresh_token, new_refresh_token)
    
    return LoginResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=900
    )


@router.post("/register")
async def register(request: RegisterRequest, user_service: UserService = Depends()):
    """Register a new user account."""
    existing = await user_service.get_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await user_service.create_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name
    )
    
    return {"message": "Registration successful", "user_id": user.id}


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """Logout and invalidate tokens."""
    payload = decode_token(token)
    if payload:
        await user_service.revoke_all_tokens(payload.get("sub"))
    return {"message": "Logged out successfully"}


@router.post("/google")
async def google_login(request: GoogleLoginRequest, user_service: UserService = Depends()):
    """
    Login with Google OAuth.
    SCRUM-12: Add social login with Google and Apple
    """
    # Verify Google ID token and get user info
    google_user = await user_service.verify_google_token(request.id_token)
    if not google_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")
    
    # Find or create user
    user = await user_service.find_or_create_google_user(google_user)
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return LoginResponse(access_token=access_token, refresh_token=refresh_token, expires_in=900)


@router.post("/apple")
async def apple_login(request: AppleLoginRequest, user_service: UserService = Depends()):
    """
    Login with Apple Sign In.
    SCRUM-12: Add social login with Google and Apple
    """
    apple_user = await user_service.verify_apple_token(request.id_token)
    if not apple_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Apple token")
    
    user = await user_service.find_or_create_apple_user(apple_user, request.user_info)
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return LoginResponse(access_token=access_token, refresh_token=refresh_token, expires_in=900)
