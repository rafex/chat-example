from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    WEATHER = "weather"

class Message(BaseModel):
    """Mensaje en el chat"""
    type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[dict] = None

class ChatSession(BaseModel):
    """Sesión de chat"""
    id: str
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.now)
    location: Optional[str] = None

    def add_message(self, message_type: MessageType, content: str, data: Optional[dict] = None):
        """Añadir mensaje a la sesión"""
        message = Message(type=message_type, content=content, data=data)
        self.messages.append(message)
        return message

    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Obtener mensajes recientes"""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages
