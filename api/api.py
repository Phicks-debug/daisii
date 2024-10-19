import os
import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from aws_services.bedrock import BedrockService
from aws_services.dynamodb import DynamoDBService
from aws_services.rds import AuroraPostgres

from prompt import INSTRUCTION_VERSION_1, INSTRUCTION_TITAN_VERSION

memory = []

load_dotenv()

app = FastAPI()
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.environ.get("DESTINATION_API_URL")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
bedrock_service = BedrockService(
    os.environ.get("BEDROCK_REGION")
)
dynamodb_service = DynamoDBService(
    os.environ.get("DYNAMODB_REGION"), 
    os.environ.get("DYNAMODB_TABLE_NAME")
)
user_database = AuroraPostgres(
    os.environ.get('AURORA_DATABASE_REGION')
)


@app.post("/register")
async def register_user(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        username = data.get("username")
        password = data.get("password")
        if not username or not password or not email:
            raise HTTPException(status_code=400, detail="All data field (email, username, password) must required")
        await user_database.create_new_user(email, username, password)
        return {"message": f"User {email} registered successfully"}
    except Exception as e:
        logging.error(f"Error in register_user endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/login")
async def login_user(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        user = await user_database.get_user(email, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"message": f"User {email} login successful"}
    except Exception as e:
        logging.error(f"Error in login_user endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/create_table/{conversation_id}")
async def create_table(conversation_id: str):
    await dynamodb_service.create_table(conversation_id)
    return {"message": "Table created successfully"}


@app.get("/chat/{userid}")
async def get_chat_history(userid: str):
    try:
        chat_history = await dynamodb_service.get_chat_history(userid)
        return chat_history
    except Exception as e:
        logging.error(f"Error in get_chat_history endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/chat")
async def chat(request: Request):
    try:
        # # Generate a unique conversation ID (you might want to implement a better way to manage this)
        # conversation_id = "temp_conversation_id"

        # # Retrieve chat history
        # chat_history = await dynamodb_service.get_chat_history(conversation_id)
        
        # # Add the new message to the chat history
        # chat_history.append(message.dict())
        
        # Call Bedrock to get the streaming response
        data = await request.json()
        prompt = bedrock_service.format_llama_prompt(data["content"], INSTRUCTION_VERSION_1)
        # memory.append(data)
        # stream = await bedrock_service.invoke_model_claude(
            # INSTRUCTION_VERSION_1, 
            # memory, 
            # 1024, 
            # 0, 
            # 0.99, 
            # 0
        # )
        # stream = await bedrock_service.invoke_model_llama(
            # prompt, 
            # 1024, 
            # 0, 
            # 0.99
        # )
        stream = await bedrock_service.invoke_model_titan(
            INSTRUCTION_TITAN_VERSION.format(question=data["content"]), 
            1024, 
            0, 
            0.99
        )
        
        async def generate():
            full_response = ""
            try:
                # # Parse Claude stream response
                # for event in stream:
                #     chunk = json.loads(event["chunk"]["bytes"])
                #     if chunk['type'] == 'content_block_delta':
                #         if chunk['delta']['type'] == 'text_delta':
                #             text_chunk = chunk['delta']['text']
                #             yield text_chunk
                #             full_response+=text_chunk
                
                # Parse Llama stream response    
                # for event in stream:
                #     chunk = json.loads(event["chunk"]["bytes"])
                #     text = chunk["generation"]
                #     yield text
                #     full_response += text
                
                # Parse Titan stream response
                for event in stream:
                    chunk = json.loads(event["chunk"]["bytes"])
                    text = chunk["outputText"]
                    yield text
                    full_response += text
                            
            except Exception as e:
                logging.error(f"Error while streaming response: {str(e)}")
                raise HTTPException(status_code=500, detail="Error while streaming response")
            
            # Save the updated chat history
            # memory.append({"role": "assistant", "content": full_response})
            # chat_history.append({"role": "assistant", "content": full_response})
            # await dynamodb_service.save_chat_history(conversation_id, chat_history)

        return StreamingResponse(generate(), media_type="text/markdown")
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8001, log_level="info")