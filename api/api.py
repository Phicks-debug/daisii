import json
import logging
import pytz

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from bedrock_service import BedrockService
from dynamodb_service import DynamoDBService
from datetime import datetime

instruction = f"""
- You have access to the real time. You know what time it is right now.
- The current real time is: {datetime.now(tz = pytz.timezone("Asia/Bangkok")).strftime('%Y-%m-%d %H:%M:%S %Z')}

<role>
Your name is Daisii. 
You are friend of Gracii, another very smart and decisive AI.
DO NOT call yourself Claude or mention anything about Anthropic company.
You are Daisii.
You can speak well Vietnamese, English.
Main language is English.
</role>

<instruction>
- Always double check your answer, and thinking thoroughly.
- Give clear, on ppint, short answer .
- If you do not know the answer, please say "I don't know". Do not give false information.
- Always ask the user if you feel the question is unclear or you need more information.
<instruction>
"""

memory = []

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
bedrock_service = BedrockService("us-east-1")
dynamodb_service = DynamoDBService("us-east-1", "chat_history")


@app.post("/create_table/{conversation_id}")
async def create_table(conversation_id: str):
    await dynamodb_service.create_table(conversation_id)
    return {"message": "Table created successfully"}


@app.post("/chat")
async def chat(request: Request):
    # try:
        # # Generate a unique conversation ID (you might want to implement a better way to manage this)
        # conversation_id = "temp_conversation_id"

        # # Retrieve chat history
        # chat_history = await dynamodb_service.get_chat_history(conversation_id)
        
        # # Add the new message to the chat history
        # chat_history.append(message.dict())
        
        # Call Bedrock to get the streaming response
        data = await request.json()
        memory.append(data)
        stream = await bedrock_service.invoke_model(instruction, memory, 512, 0, 0.9, 0)
        
        async def generate():
            full_response = ""
            try:
                for event in stream:
                    chunk = json.loads(event["chunk"]["bytes"])
                    if chunk['type'] == 'content_block_delta':
                        if chunk['delta']['type'] == 'text_delta':
                            text_chunk = chunk['delta']['text']
                            yield text_chunk
                            full_response+=text_chunk
            except Exception as e:
                logging.error(f"Error while streaming response: {str(e)}")
                raise HTTPException(status_code=500, detail="Error while streaming response")
            
            # Save the updated chat history
            memory.append({"role": "assistant", "content": full_response})
            # chat_history.append({"role": "assistant", "content": full_response})
            # await dynamodb_service.save_chat_history(conversation_id, chat_history)

        return StreamingResponse(generate(), media_type="text/markdown")
    # except Exception as e:
    #     logging.error(f"Error in chat endpoint: {str(e)}")
    #     raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8001, log_level="info")