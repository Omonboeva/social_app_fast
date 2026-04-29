from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ---- USER ----
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- TOKEN ----
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- CHAT ----
class ChatCreate(BaseModel):
    name: Optional[str] = None        # Guruh nomi
    is_group: bool = False
    member_ids: list[int]             # A'zolar ID lari

class ChatOut(BaseModel):
    id: int
    name: Optional[str]
    is_group: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---- MESSAGE ----
class MessageCreate(BaseModel):
    text: str

class MessageOut(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    sender_username: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True