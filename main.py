from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import init_db
from routers.auth_router import router as auth_router
from routers.chat_router import router as chat_router
from routers.message_router import router as message_router
from routers.ws_router import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="ChatApp",
    description="Sodda FastAPI Chat ilovasi",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(message_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"message": "ChatApp ishlayapti!", "docs": "/docs"}