from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..core.utils import validate_nitj_email, send_otp_email
import random
from datetime import datetime, timedelta
from jose import JWTError, jwt
from ..core.config import settings
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal
from passlib.context import CryptContext

# We merge them into one clean "SignupRequest"
class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    # Literal forces the value to be only one of these two
    role: Literal["student", "professor"] 

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        # Check for at least one digit, one uppercase, and one special char
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Temporary in-memory store for OTPs
# Note: In Phase 4, we'll move this to Redis or a DB table
otp_store = {}
user_data_store = {}



# Set up Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/signup")
async def signup(request: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Normalize Email
    email = request.email.lower()
    
    # 2. Check Database first (Efficiency: don't send mail to existing users)
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 3. Rest of the logic...
    if not validate_nitj_email(email):
         raise HTTPException(status_code=400, detail="Only @nitj.ac.in allowed")

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    
    # Store hashed password immediately so plain text never sits in RAM
    user_data_store[email] = {
        "name": request.name,
        "password_hash": pwd_context.hash(request.password), 
        "role": request.role
    }

    background_tasks.add_task(send_otp_email, email, otp)
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
async def verify_otp(email: str, code: str, db: Session = Depends(get_db)):
    email_lower = email.lower() # Normalize here too!

    if otp_store.get(email_lower) == code:
        data = user_data_store.get(email_lower)
        if not data:
            raise HTTPException(status_code=400, detail="User data expired.")

        # 3. Create the User in Postgres
        new_user = User(
            name=data['name'],
            email=email_lower,
            # Use the hash we stored in user_data_store during signup
            password_hash=data['password_hash'], 
            role=data['role']
        )
        
        db.add(new_user)
        db.commit()
        
        # 4. Clean up
        del otp_store[email_lower]
        del user_data_store[email_lower]
        
        return {"message": "Account activated and saved to database!"}
    
    raise HTTPException(status_code=400, detail="Invalid or expired OTP.")


# Helper to create the JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Create a Login model for better Swagger UI support and JSON security
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. OAuth2PasswordRequestForm uses 'username' as the field name (even for emails)
    email_lower = form_data.username.lower()
    
    # 2. Fetch user from DB
    user = db.query(User).filter(User.email == email_lower).first()    
    
    # 3. Verify existence and password using Bcrypt
    # Use 'form_data.password' here, NOT 'request.password'
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Generate Token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": str(user.id)}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role
    }

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token using our Secret Key
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user