from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import logging
from bedrock_service import BedrockService
from dynamodb_service import DynamoDBService

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
bedrock_service = BedrockService("us-west-2")
dynamodb_service = DynamoDBService("us-west-2", "chat_history")

class ChatMessage(BaseModel):
    role: str
    content: str

@app.post("/create_table/{conversation_id}")
async def create_table(conversation_id: str):
    await dynamodb_service.create_table(conversation_id)
    return {"message": "Table created successfully"}

@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        # Generate a unique conversation ID (you might want to implement a better way to manage this)
        conversation_id = "temp_conversation_id"

        # Retrieve chat history
        chat_history = await dynamodb_service.get_chat_history(conversation_id)
        
        # Add the new message to the chat history
        chat_history.append(message.dict())
        
        # Call Bedrock to get the streaming response
        stream = await bedrock_service.invoke_model(chat_history)
        
        async def generate():
            full_response = ""
            try:
                async for chunk in stream:
                    if chunk:
                        content = json.loads(chunk.get('chunk', {}).get('bytes', b'{}').decode())['completion']
                        full_response += content
                        yield content
            except Exception as e:
                logging.error(f"Error while streaming response: {str(e)}")
                raise HTTPException(status_code=500, detail="Error while streaming response")
            
            # Save the updated chat history
            chat_history.append({"role": "assistant", "content": full_response})
            await dynamodb_service.save_chat_history(conversation_id, chat_history)

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Run API on port 8001