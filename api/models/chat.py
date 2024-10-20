from enum import Enum
from typing import List, Dict
from fastapi import BackgroundTasks
from pydantic import BaseModel


class MediaType(str, Enum):
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    WEBP = "image/webp"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TOOLUSE = "tool_use"
    TOOLRESULT = "tool_result"
    

class Image(BaseModel):
    type = "base64"
    media_type: MediaType
    data: str
    
    
class TextContent(BaseModel):
    type: ContentType.TEXT
    text: str
    

class ImageContent(BaseModel):
    type: ContentType.IMAGE
    source: Image
    
    
class ToolUseContent(BaseModel):
    type: ContentType.TOOLUSE
    tool_use_id: str
    tool_name: str
    input: Dict
    

class ToolResultContent(BaseModel):
    type: ContentType.TOOLRESULT
    tool_use_id: str
    is_error: bool
    content: List[TextContent | ImageContent] | str


class ChatMessage(BaseModel):
    role: str
    content: List[TextContent | ImageContent | ToolUseContent | ToolResultContent] | str


class ChatHistory(BaseModel):
    conversation_id: str
    user_id: str
    messages: List[ChatMessage]

    
class ChatService:
    def __init__(self, redis_client, dynamodb_service):
        self.redis = redis_client
        self.dynamodb = dynamodb_service
        self.cache_ttl = 3600  # 1 hour cache


    async def get_chat_history(self, user_id: str, conversation_id: str) -> ChatHistory:
        # Try getting from Redis first
        cache_key = f"chat:{user_id}:{conversation_id}"
        cached_history = self.redis.get(cache_key)
        
        if cached_history:
            return ChatHistory.model_validate(cached_history)

        # If not in cache, get from DynamoDB
        history = await self.dynamodb.get_chat_history(user_id, conversation_id)
        
        # Cache the result
        self.redis.setex(
            cache_key,
            self.cache_ttl,
            history.json()
        )
        
        return history


    async def save_chat_history(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[ChatMessage],
        background_tasks: BackgroundTasks
    ):
        # Update cache immediately
        cache_key = f"chat:{user_id}:{conversation_id}"
        history = ChatHistory(
            conversation_id=conversation_id,
            user_id=user_id,
            messages=messages
        )
        self.redis.setex(cache_key, self.cache_ttl, history.model_dump_json())
        
        # Save to DynamoDB in background
        background_tasks.add_task(
            self.dynamodb.save_chat_history,
            conversation_id,
            user_id,
            messages
        )