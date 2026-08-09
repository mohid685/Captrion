from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdateRequest(BaseModel):
    risk_tolerance: str | None = Field(default=None, pattern="^(low|moderate|high)$")
    investment_goals: str | None = None
    preferred_sectors: str | None = None


class ProfileResponse(BaseModel):
    risk_tolerance: str | None
    investment_goals: str | None
    preferred_sectors: str | None