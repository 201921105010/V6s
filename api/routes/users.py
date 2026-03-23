from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from crud.users import get_all_users, save_all_users, create_pending_user, user_exists

router = APIRouter()

@router.get("/")
def list_users():
    """Get all users."""
    try:
        df = get_all_users()
        df = df.where(df.notnull(), None)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
def replace_users(data: List[Dict[str, Any]]):
    """Replace all users."""
    import pandas as pd
    try:
        df = pd.DataFrame(data)
        success = save_all_users(df)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save users")
        return {"message": "Users updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from typing import Literal

from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    role: Literal["Boss", "Admin", "Sales", "Prod"]
    name: str = Field(min_length=1, max_length=64)

    @field_validator("username", "password", "name")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value

@router.post("/register")
def register_user(user: UserCreate):
    """Register a new pending user."""
    try:
        if user_exists(user.username):
            raise HTTPException(status_code=400, detail="User already exists")
        
        new_row = create_pending_user(
            username=user.username,
            password=user.password,
            role=user.role,
            name=user.name
        )
        return {"message": "User registered successfully", "data": new_row}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
