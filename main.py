from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Mapping

from dataclasses_json import config, dataclass_json
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from marshmallow import fields

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@dataclass_json
@dataclass
class ChatMessage:
    author: str
    message: str
    timestamp: datetime = field(
        default_factory=datetime.now,
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        )
    )


class MessagePubSub:
    def __init__(self):
        self.subscribers: List[WebSocket] = []

    def subscribe(self, listener: WebSocket):
        self.subscribers.append(listener)

    def unsubscribe(self, listener: WebSocket):
        self.subscribers.remove(listener)

    async def publish(self, msg: ChatMessage):
        for subscriber in self.subscribers:
            await subscriber.send_json(msg.to_dict())


@dataclass
class ChatApp:
    pubsub: MessagePubSub
    app: FastAPI
    messages: List[ChatMessage] = field(default_factory=list)

    async def receive_message(self, message):
        self.messages.append(message)
        await self.pubsub.publish(message)


pubsub = MessagePubSub()
chat = ChatApp(pubsub=pubsub, app=app)


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/history")
async def history() -> JSONResponse:
    return JSONResponse(content=[message.to_dict() for message in chat.messages])


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pubsub.subscribe(websocket)
    try:
        while True:
            message = ChatMessage.from_dict(await websocket.receive_json())
            await chat.receive_message(message)
    finally:
        pubsub.unsubscribe(websocket)
