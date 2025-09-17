# src/server/models/api.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# Request Models (Input)
class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    native_language: str = Field(..., min_length=2, max_length=5, example="de")

class SentenceCreateRequest(BaseModel):
    original_text: str = Field(..., min_length=1, max_length=200, example="Ich lerne Deutsch")
    category: Optional[str] = Field(None, max_length=50, example="Lernen")
    user_id: int = Field(..., gt=0, example=1)

class TranslationCreateRequest(BaseModel):
    sentence_id: int = Field(..., gt=0, example=1)
    target_language: str = Field(..., min_length=2, max_length=5, example="en")
    # translated_text würde normalerweise vom AI-Service kommen

class LearningAttemptRequest(BaseModel):
    translation_id: int = Field(..., gt=0, example=1)
    user_answer: str = Field(..., min_length=1, example="I learn German")

# Response Models (Output)
class UserResponse(BaseModel):
    id: int
    username: str
    native_language: str
    created_at: datetime

    class Config:
        orm_mode = True  

class SentenceResponse(BaseModel):
    id: int
    user_id: int
    original_text: str
    language_code: str
    category: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

class TranslationResponse(BaseModel):
    id: int
    sentence_id: int
    translated_text: str
    target_language_code: str
    group_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ProgressGroupResponse(BaseModel):
    id: int
    sentence_id: int
    user_id: int
    group_score: float
    next_review: Optional[datetime]
    last_reviewed: Optional[datetime]
    review_count: int
    created_at: datetime

    class Config:
        orm_mode = True

class LearningProgressResponse(BaseModel):
    id: int
    user_id: int
    translation_id: int
    group_id: int
    score: int
    last_reviewed: Optional[datetime]
    next_review: Optional[datetime]
    review_count: int
    success_rate: int

    class Config:
        orm_mode = True

# Additional Models
class SupportedLanguageResponse(BaseModel):
    code: str
    name: str

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None