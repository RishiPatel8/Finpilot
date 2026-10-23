from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = Field(default="salaried", description="student, salaried, freelancer, business_owner")
    auth_provider: str = "local"


class UserCreate(UserBase):
    password: Optional[str] = Field(default=None, min_length=8, description="Minimum 8 characters password for local accounts")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class FirebaseLoginRequest(BaseModel):
    id_token: str
    role: Optional[str] = Field(default="salaried")
    link_password: Optional[str] = Field(default=None, description="Password required to link an existing local account with the same email")


class LinkAccountRequest(BaseModel):
    id_token: str
    password: str = Field(description="Existing account password to verify ownership before linking")


class UserResponse(UserBase):
    id: str
    firebase_uid: Optional[str] = None
    auth_provider: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[str] = None
