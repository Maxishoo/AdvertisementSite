from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+7\d{10}$')
    username: str = Field(..., min_length=3)
    first_name: Optional[str] = "not filled in"
    last_name: Optional[str] = "not filled in"
    role: Optional[str] = "user"
    is_verified: Optional[bool] = False
    is_banned: Optional[bool] = False
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+7\d{10}$')
    username: Optional[str] = Field(None, min_length=3)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_verified: Optional[bool] = None
    is_banned: Optional[bool] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserInDB(UserBase):
    id: UUID
    created_at: datetime
    last_login: Optional[datetime] = None
    password_hash: str

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    role: str
    created_at: datetime
    is_verified: bool
    is_banned: bool
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
