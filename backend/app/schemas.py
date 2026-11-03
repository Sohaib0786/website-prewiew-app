from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SiteCreate(BaseModel):
    url: str = Field(min_length=3, max_length=2048)


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    title: Optional[str] = None
    preview_type: str
    created_at: datetime
    preview_file: str = Field(exclude=True)

    @computed_field
    @property
    def preview_url(self) -> str:
        return f"/previews/{self.preview_file}"
