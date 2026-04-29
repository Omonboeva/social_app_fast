from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import Chat, ChatMember, User
from schemas import ChatCreate, ChatOut
from auth import get_current_user

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post("/", response_model=ChatOut)
async def create_chat(data: ChatCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    chat = Chat(name=data.name, is_group=data.is_group)
    db.add(chat)
    await db.flush()


    db.add(ChatMember(chat_id=chat.id, user_id=user.id, is_admin=True))


    for uid in data.member_ids:
        if uid != user.id:
            db.add(ChatMember(chat_id=chat.id, user_id=uid))

    await db.commit()
    await db.refresh(chat)
    return chat


@router.get("/", response_model=list[ChatOut])
async def my_chats(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Chat)
        .join(ChatMember, Chat.id == ChatMember.chat_id)
        .where(ChatMember.user_id == user.id)
    )
    return result.scalars().all()


@router.get("/{chat_id}", response_model=ChatOut)
async def get_chat(chat_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(403, "Bu chatga kirishingiz yo'q")

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(404, "Chat topilmadi")
    return chat


@router.post("/{chat_id}/members/{user_id}")
async def add_member(chat_id: int, user_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user.id, ChatMember.is_admin == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(403, "Faqat admin a'zo qo'sha oladi")

    db.add(ChatMember(chat_id=chat_id, user_id=user_id))
    await db.commit()
    return {"detail": "A'zo qo'shildi"}


@router.delete("/{chat_id}/leave")
async def leave_chat(chat_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user.id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "A'zo emassiz")

    await db.delete(member)
    await db.commit()
    return {"detail": "Chatdan chiqdingiz"}