from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from database import get_db
from models import User
from schemas import UserRegister, UserLogin, UserOut, Token
from auth import hash_password, check_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(or_(User.username == data.username, User.email == data.email))
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, "Username yoki email band")

    user = User(
        username=data.username,
        email=data.email,
        password=hash_password(data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not check_password(data.password, user.password):
        raise HTTPException(401, "Username yoki parol xato")

    return Token(access_token=create_token(user.id))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user