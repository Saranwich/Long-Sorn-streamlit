# /backend/shared/models/auth.py

from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None # | None = None หมายถึง Field นี้ไม่บังคับกรอก