from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import json

from database import SessionLocal as AsyncSessionLocal
from models import Message, ChatMember
from auth import create_token
from jose import jwt, JWTError

SECRET_KEY = "bd73916ae06dedb0496a2aa92c8aa553a3eff65560a44b2f137f41a84df2a18a"
ALGORITHM = "HS256"

router = APIRouter(tags=["WebSocket"])


connections: dict[int, dict[int, WebSocket]] = {}


async def get_user_id_from_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError):
        return None


@router.websocket("/ws/{chat_id}")
async def websocket_chat(
    websocket: WebSocket,
    chat_id: int,
    token: str = Query(...)
):
    user_id = await get_user_id_from_token(token)
    if not user_id:
        await websocket.close(code=4001)
        return


    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
        )
        if not result.scalar_one_or_none():
            await websocket.close(code=4003)
            return

    await websocket.accept()


    if chat_id not in connections:
        connections[chat_id] = {}
    connections[chat_id][user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
                text = payload.get("text", "").strip()
            except Exception:
                continue

            if not text:
                continue


            async with AsyncSessionLocal() as db:
                from models import User
                user_result = await db.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()

                msg = Message(chat_id=chat_id, sender_id=user_id, text=text)
                db.add(msg)
                await db.commit()
                await db.refresh(msg)


            out = json.dumps({
                "id": msg.id,
                "chat_id": chat_id,
                "sender_id": user_id,
                "sender": user.username if user else "?",
                "text": text,
                "created_at": msg.created_at.isoformat(),
            })

            dead = []
            for uid, ws in connections.get(chat_id, {}).items():
                try:
                    await ws.send_text(out)
                except Exception:
                    dead.append(uid)

            for uid in dead:
                connections[chat_id].pop(uid, None)

    except WebSocketDisconnect:
        connections.get(chat_id, {}).pop(user_id, None)