import os
import utils
import logging

from datetime import timedelta
from dotenv import load_dotenv
from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from jwt.exceptions import InvalidTokenError
from pydantic import EmailStr
from redis import ConnectionPool, Redis

from aws_services.bedrock import BedrockService
from aws_services.dynamodb import DynamoDBService
from aws_services.rds import AuroraPostgres
from models.authentication import Authentication
from models.session import Session, TokenData, Token
from models.user import User, UserInDB, RegisterUser
from models.chat import ChatMessage, ChatService

from prompt import INSTRUCTION_CLAUDE_VERSION, \
                INSTRUCTION_DAISII_VERSION, \
                INSTRUCTION_TITAN_VERSION
from config import CLAUDE, DAISII, TITAN


load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
session = Session(
    os.environ.get("SECRET_KEY"),
    os.environ.get("ALGORITHM")
)
authentication = Authentication()

# Add Redis for caching
pool = ConnectionPool(
    host=os.environ.get("REDIS_HOST"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    socket_connect_timeout=10
)
redis_client = Redis(connection_pool=pool)
chat_service = ChatService(redis_client, dynamodb_service)


async def get_user(
    rds: AuroraPostgres, 
    email: EmailStr
):  
    # Create a cache and check for user
    cache_key = f"user:{email}"
    cached_user = redis_client.get(cache_key)
    
    if cached_user:
        return UserInDB.model_validate_json(cached_user)
    
    #  If not search the database
    result = await rds.get_user(email)
    if result["status"] == "Error":
        raise HTTPException(
                status_code=401,
                detail=f"Incorrect email. Error: {result['message']}"
            )
    if result["message"]:
        user = UserInDB(
            id=result["message"][0][0]["stringValue"],
            email=result["message"][0][1]["stringValue"],
            username=result["message"][0][2]["stringValue"],
            password=result["message"][0][3]["stringValue"],
            disabled=result["message"][0][4]["booleanValue"]
        )
        redis_client.setex(cache_key, 3600, user.model_dump_json())
        return user
    else:
        return False


async def authenticate_user(
    authen: Authentication,
    rds: AuroraPostgres, 
    email: EmailStr, 
    plain_password: str
):
    user = await get_user(rds, email)
    if not user:
        return False
    if not authen.verify_password(
        plain_password, 
        user.password
    ):
        return False
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = session.decode(token)
        email: EmailStr = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    
    user = await get_user(
        rds=user_database, 
        email=token_data.email
    )
    
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = await authenticate_user(
        authentication,
        user_database, 
        form_data.username, 
        form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))
    )
    access_token = session.create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/register")
async def register_user(
    user: RegisterUser
):
    try:
        # Ensure all fields are provided
        if not user.username or not user.password or not user.email:
            raise HTTPException(
                status_code=400, 
                detail="All data fields (email, username, password) are required"
            )

        # Validate password matching
        user.verify_passwords_match()

        # Hash the password before saving it
        hashed_password = authentication.get_password_hash(user.password)

        # Register the user in the database
        result = await user_database.create_new_user(
            user.email, 
            user.username, 
            hashed_password
        )
        
        if result["status"] == "Error":
            raise HTTPException(
                status_code=500,
                detail=result["message"]
            )

        return {
            "message": f"User {user.email} registered successfully"
        }
    except Exception as e:
        logging.error(f"Error in register_user endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@app.post("/chat/create/{conversation_id}")
async def create_new_conversation(
    conversation_id: str,
    user: UserInDB = Depends(get_current_active_user)
):
    await dynamodb_service.create_table(
        user.id,
        conversation_id
    )
    return {"message": "Table created successfully"}


@app.get("/chat/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    user: UserInDB = Depends(get_current_active_user)
):
    try:
        chat_history = await chat_service.get_chat_history(user.id, conversation_id)
        return chat_history
    except Exception as e:
        logging.error(f"Error in get_chat_history endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@app.post("/chat/{conversation_id}")
async def chat(
    conversation_id: str,
    messages: List[ChatMessage],
    model: str,
    background_tasks: BackgroundTasks,
    user: UserInDB = Depends(get_current_active_user)
):
    try:
        if model == CLAUDE:
            stream = await bedrock_service.invoke_model_claude(
                INSTRUCTION_CLAUDE_VERSION, 
                messages=messages, 
                max_token=1024, 
                temp=0, 
                p=0.99, 
                k=0
            )
        elif model == DAISII:
            prompt = bedrock_service.format_llama_prompt(
                messages, INSTRUCTION_DAISII_VERSION
            )
            stream = await bedrock_service.invoke_model_llama(prompt, 1024, 0, 0.99)
        elif model == TITAN:
            prompt = bedrock_service.format_titan_prompt(
                messages, INSTRUCTION_TITAN_VERSION
            )
            stream = await bedrock_service.invoke_model_titan(prompt, 1024, 0, 0.99)
        else:
            logging.error(f"Invalid model specified from parameter")
            raise HTTPException(status_code=400, detail="Invalid model specified")
        
        async def generate(model_type):
            full_response = ""
            try:
                async for chunk in utils.process_stream(stream, model_type):
                    yield chunk
                    full_response += chunk
                
                # Update messages with assistant's response
                messages.append(ChatMessage(
                    role="assistant",
                    content=full_response
                ))
                
                # Save chat history in background
                await chat_service.save_chat_history(
                    user.id,
                    conversation_id,
                    messages,
                    background_tasks
                )
                            
            except Exception as e:
                logging.error(f"Error while streaming response: {str(e)}")
                raise HTTPException(status_code=500, detail="Error while streaming response")

        return StreamingResponse(generate(model), media_type="text/markdown")
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8001, log_level="info")