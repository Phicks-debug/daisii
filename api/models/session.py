import jwt

from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from jwt.exceptions import InvalidTokenError

from typing import Dict


class TokenData(BaseModel):
    email: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str
    

class Session:
    def __init__(self, secret_key, algorithm):
        self.secret_key = secret_key
        self.algorithm = algorithm


    def  __encode(self, payload):
        return jwt.encode(
            payload, 
            self.secret_key, 
            algorithm=self.algorithm
        )


    def  decode(self, token):
        try:
            return jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
        except InvalidTokenError:
            return None
        
    
    def create_access_token(self, 
            data: Dict, 
            expires_delta: timedelta | None = None
        ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = self.__encode(to_encode)
        return encoded_jwt