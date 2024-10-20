from pydantic import BaseModel, EmailStr
from fastapi import HTTPException


class User(BaseModel):
    id: str
    email: EmailStr | None = None
    username: str
    disabled: bool | None = None


class UserInDB(User):
    password: str
    

class RegisterUser(BaseModel):
    email: EmailStr
    username: str
    password: str
    verify_password: str
    
    def verify_passwords_match(self):
        if self.password != self.verify_password:
            raise HTTPException(
                status_code=400, 
                detail="Passwords do not match"
            )