from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime



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



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"



class ChatCreate(BaseModel):
    name: Optional[str] = None
    is_group: bool = False
    member_ids: list[int]

class ChatOut(BaseModel):
    id: int
    name: Optional[str]
    is_group: bool
    created_at: datetime

    class Config:
        from_attributes = True



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