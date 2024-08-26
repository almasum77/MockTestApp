from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr  # Using EmailStr to ensure the email is valid
    password: str
    
class User(BaseModel):
    userid: int
    email: str
    firstname: str
    lastname: str
    createddate: datetime
    createdby: Optional[int] = None
    
    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdatePassword(BaseModel):
    user_id: int
    current_password: str
    new_password: str
   
    # Optional: Add password validation here (e.g., length, complexity)
    class Config:
        orm_mode = True

class QuestionAnswerPair(BaseModel):
    question: str
    question_type: str
    answer: str

    class Config:
        extra = "ignore"
        
class QuestionAnswerPairNew(BaseModel):
    question_id: int
    question: str
    question_type: str
    answer: str

    class Config:
        extra = "ignore"

class SaveQuestionsAndAnswersRequest(BaseModel):
    fileid: int
    question_answer_pairs: List[QuestionAnswerPair]
    
class FileResponse(BaseModel):
    fileid: int
    filename: str
    
class FileQuestionSummary(BaseModel):
    file_id: int
    original_filename: str
    number_of_questions: int
    uploaddate: datetime
    
    
## for testing methods


class UserAnswerSubmission(BaseModel):
    question_id: int
    answer: Optional[str]  # Allow null values

    class Config:
        extra = "ignore"
    

class TestResult(BaseModel):
    score: int
    total_questions: int
    correct_answers: int

    class Config:
        orm_mode = True

class SubmitAnswersRequest(BaseModel):
    fileid: int
    score: int
    total_questions: int
    correct_answers: int
    question_type: str
    user_answers: List[UserAnswerSubmission]