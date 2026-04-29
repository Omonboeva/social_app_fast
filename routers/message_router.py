from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import Message, ChatMember, User
from schemas import MessageCreate, MessageOut
from auth import get_current_user

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["Messages"])


async def check_member(chat_id: int, user_id: int, db: AsyncSession):
    result = await db.execute(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(403, "Bu chatga kirishingiz yo'q")


@router.get("/", response_model=list[MessageOut])
async def get_messages(chat_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await check_member(chat_id, user.id, db)

    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .options(selectinload(Message.sender))
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    return [
        MessageOut(
            id=m.id,
            chat_id=m.chat_id,
            sender_id=m.sender_id,
            sender_username=m.sender.username,
            text=m.text,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/", response_model=MessageOut)
async def send_message(chat_id: int, data: MessageCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await check_member(chat_id, user.id, db)

    msg = Message(chat_id=chat_id, sender_id=user.id, text=data.text)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return MessageOut(
        id=msg.id,
        chat_id=msg.chat_id,
        sender_id=msg.sender_id,
        sender_username=user.username,
        text=msg.text,
        created_at=msg.created_at,
    )


@router.delete("/{message_id}")
async def delete_message(chat_id: int, message_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Message).where(Message.id == message_id, Message.chat_id == chat_id))
    msg = result.scalar_one_or_none()

    if not msg:
        raise HTTPException(404, "Xabar topilmadi")
    if msg.sender_id != user.id:
        raise HTTPException(403, "Faqat o'z xabaringizni o'chira olasiz")

    await db.delete(msg)
    await db.commit()
    return {"detail": "Xabar o'chirildi"}