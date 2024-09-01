import random
from fastapi import FastAPI, File, UploadFile, Request,Depends, HTTPException, status, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import ValidationError
import spacy
from sqlalchemy import func
from transformers import pipeline
import uuid
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from src.database import models, schemas
from src.database.models import Question, UploadedFile
from .tables_create import User
from .database.database import engine, SessionLocal
from datetime import datetime, timedelta
import jwt
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os
from typing import List
import logging
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

# Create the database tables
models.Base.metadata.create_all(bind=engine)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if the email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    # hashed_password = user.password
    db_user = models.User(email=user.email, hashedpassword=hashed_password, firstname=user.firstname,lastname=user.lastname)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY", "default_fallback_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials======&&&&",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@app.post("/login/")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not verify_password(user.password, db_user.hashedpassword):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}



#password hass part
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Set up NLP and paraphrasing pipeline
nlp = spacy.load("en_core_web_sm")
paraphraser = pipeline("text2text-generation", model="Vamsi/T5_Paraphrase_Paws")

# Template setup
templates = Jinja2Templates(directory="src/templates")

# In-memory storage for session data (questions and their correct answers)
questions_store = {}

@app.get("/", response_class=HTMLResponse)
async def display_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "questions": [], "answers": []})


# ================== File posting to api ===================
@app.post("/", response_class=HTMLResponse)
async def handle_file_upload(request: Request, file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode('utf-8')
    question_types = ["FillInTheBlanks", "TrueFalse"]  
    # question_types = ["FillInTheBlanks"]  
    questions, answers = generate_questions_old(text, question_types)
    session_id = str(uuid.uuid4())
    questions_store[session_id] = answers
    return templates.TemplateResponse("index.html", {
        "request": request,
        "questions": questions,
        "session_id": session_id,
        "correct_answers": answers  # Include correct answers in the context
    })




questions = []
answers = {}
# ================== generate  questions ===================
def generate_questions_old(text, question_types):
    doc = nlp(text)
    questions = []
    answers = {}
    count = 0
    for sent in doc.sents:
        if count >= 10:
            break
        paraphrased = paraphrase_sentence(sent.text)
        if not paraphrased:
            continue
        if "FillInTheBlanks" in question_types:
            # Generate fill-in-the-blank question
            fill_in_the_blank_question, answer = generate_fill_in_the_blanks_question(paraphrased)
            question_id = str(uuid.uuid4())
            questions.append({'id': question_id, 'question': fill_in_the_blank_question, 'type': 'FillInTheBlanks'})
            answers[question_id] = answer
        if "TrueFalse" in question_types:
            # Generate true/false question
            true_false_question, is_true = generate_true_false_question(paraphrased)
            question_id = str(uuid.uuid4())
            questions.append({'id': question_id, 'question': true_false_question, 'type': 'TrueFalse'})
            answers[question_id] = is_true
        count += 1
    return questions, answers

# ================== paraphrase sentance function ===================
def paraphrase_sentence(sentence):
    try:
        paraphrase_prompt = f"paraphrase: {sentence} </s>"
        paraphrased_results = paraphraser(paraphrase_prompt, max_length=100)
        # return paraphrased_results[0]['generated_text'] if paraphrased_results else None
        return paraphrased_results[0]['generated_text'] if paraphrased_results else None
    except Exception as e:
        print(f"An error occurred during paraphrasing: {e}")
        return None



# ================== generate fill in the blanks questions ===================
def generate_fill_in_the_blanks_question(paraphrased):
    # This should be a robust method to select suitable words to be replaced with blanks
    doc = nlp(paraphrased)
    entities = [ent for ent in doc.ents if ent.label_ in {'PERSON', 'ORG', 'GPE', 'LOC', 'DATE', 'EVENT'}]
    if entities:
        # Replace the first entity with a blank
        first_entity = entities[0]
        fill_in_the_blank_question = paraphrased.replace(first_entity.text, '______', 1)
        return fill_in_the_blank_question, first_entity.text
    return paraphrased, None  # Default return if no entities are found



# ================== generate true false questions ===================
def generate_true_false_question_old(paraphrased):
    # Decide randomly whether the statement should be true or false
    is_true = random.choice([True, False])
    
    if is_true:
        # Return the original paraphrased sentence as a true statement
        return f"True or False: {paraphrased}", is_true
    else:
        # Negate the sentence to make a false statement
        false_statement = negate_sentence(paraphrased)
        return f"True or False: {false_statement}", is_true


def generate_true_false_question(paraphrased):
    # Decide randomly whether the statement should be true or false
    is_true = random.choice([True, False])
    
    if is_true:
        # Return the original paraphrased sentence as a true statement
        return f"{paraphrased}", is_true
    else:
        # Negate the sentence to make a false statement
        false_statement = negate_sentence(paraphrased)
        return f"{false_statement}", is_true

# ============Implement a more sophisticated method for generating false statements===============
def negate_sentence(sentence):
    doc = nlp(sentence)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    adjectives = [token.text for token in doc if token.pos_ == 'ADJ']

    # Simple replacements for demonstration
    city_replacements = {'London': 'Paris', 'Paris': 'Rome', 'New York': 'Tokyo'}
    country_replacements = {'England': 'France', 'France': 'Italy'}
    adjective_replacements = {'beautiful': 'lovely', 'large': 'massive'}

    modified_sentence = sentence

    # Decide what to replace based on available entities and adjectives
    if entities:
        for entity_text, entity_type in entities:
            if entity_type == 'GPE':  # Geopolitical entity
                if entity_text in city_replacements:
                    modified_sentence = modified_sentence.replace(entity_text, city_replacements[entity_text])
                    break

    if adjectives:
        for adj in adjectives:
            if adj in adjective_replacements:
                modified_sentence = modified_sentence.replace(adj, adjective_replacements[adj])
                break

    return modified_sentence

# Test the function
# print(negate_sentence("London is culturally a city of immense creativity"))
# print(negate_sentence("It is a large room"))


# ================== Submit answers function ===================
@app.post("/submit-answers-old", response_class=HTMLResponse)
async def submit_answers_old(request: Request):
    form_data = await request.form()
    session_id = form_data.get('session_id')
    question_ids = [key.split('_')[1] for key in form_data.keys() if key.startswith('answers_')]
    answers = [form_data.get('answers_' + q_id) for q_id in question_ids]

    print(f"answers are: {answers}")
    print(f"question_ids are: {question_ids}")
    if session_id not in questions_store:
        return templates.TemplateResponse("index.html", {"request": request, "message": "Session expired or not found."})

    correct_answers = questions_store[session_id]
    score = 0
    
    # Print debugging information
    print(f"Question IDs: {question_ids}")
    print(f"Answers: {answers}")
    print(f"Correct Answers: {correct_answers}")

    for question_id, answer in zip(question_ids, answers):
        if question_id in correct_answers:
            correct_answer = correct_answers[question_id]
            # Check if the answer is boolean and compare directly, else perform string manipulation
            if isinstance(correct_answer, bool):
                if answer == str(correct_answer):  # Convert the correct answer to string for comparison
                    score += 1
            else:
                if answer and answer.strip().lower() == correct_answer.strip().lower():
                    score += 1
    print(f"score : {score}")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "score": score,
        "total": len(question_ids),
        "message": f"Score: {score} out of {len(correct_answers)}"
    })





# API endpoint for quesiton related tasks


@app.post("/generate-questions/", response_class=JSONResponse)
async def generate_questions_endpoint(
    file: UploadFile = File(...),
    question_size: int = Query(..., description="The number of questions to generate."),
    question_types: List[str] = Query(..., description="The types of questions to generate."),
    db: Session = Depends(get_db),  # Dependency to interact with the database
    current_user: User = Depends(get_current_user)  # Dependency to get the current user
):
    # Step 1: Use the existing function to upload and save the file
    result = await upload_and_save_file(current_user, file, db)
    saved_filename = result['saved_filename']

    
    logger.error(f"File with name {saved_filename} got from function")
    # Step 2: Retrieve the file content for question generation
    file_record = db.query(models.UploadedFile).filter(models.UploadedFile.saved_filename ==saved_filename).first()
    
    if file_record is None:
        logger.error(f"File with name {saved_filename} not found")
        raise HTTPException(status_code=404, detail="File not found")

    logger.info(f"File found: {file_record}")
    logger.info(f"File path: {file_record.filepath}")


    
    print(file_record.filepath)
    if file_record:
        file_location = file_record.filepath  # This should be correct if filepaths are stored relative to the container
        if not os.path.exists(file_location):
            raise HTTPException(status_code=404, detail="File not found")
        with open(file_location, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise HTTPException(status_code=404, detail="File not found")
    print(file_location)
    # Step 3: Open the file and read its contents
    with open(file_location, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Step 3: Generate questions and answers
    questions, answers = generate_questions(text, question_types, question_size)
    
    print("Generate questions")
    
    # Step 4: Combine questions and answers into a single list of dictionaries
    question_answer_pairs = []
    for question in questions:
        question_id = question['id']
        answer = answers.get(question_id, "")
        question_answer_pairs.append({
            "question_id": question_id,
            "question": question['question'],
            "question_type": question['type'],
            "answer": answer
        })

    # Step 5: Create a session ID for storing the questions and answers
    session_id = str(uuid.uuid4())
    questions_store[session_id] = question_answer_pairs

    # Step 6: Return the response with the fileId
    return JSONResponse({
        "file_id": file_record.fileid,
        "session_id": session_id,
        "question_answer_pairs": question_answer_pairs
    })


def generate_questions(text, question_types, question_size):
    doc = nlp(text)
    questions = []
    answers = {}
    count = 0
    
    for sent in doc.sents:
        if count >= question_size:
            break
        
        paraphrased = paraphrase_sentence(sent.text)
        if not paraphrased:
            continue
        
        if "FillInTheBlanks" in question_types:
            # Generate fill-in-the-blank question
            fill_in_the_blank_question, answer = generate_fill_in_the_blanks_question(paraphrased)
            question_id = str(uuid.uuid4())
            questions.append({'id': question_id, 'question': fill_in_the_blank_question, 'type': 'FillInTheBlanks'})
            answers[question_id] = answer  # 'answer' is already a string
        
        if "TrueFalse" in question_types:
            # Generate true/false question
            true_false_question, is_true = generate_true_false_question(paraphrased)
            question_id = str(uuid.uuid4())
            questions.append({'id': question_id, 'question': true_false_question, 'type': 'TrueFalse'})
            answers[question_id] = "True" if is_true else "False"  # Convert boolean to string
        
        count += 1
    
    return questions, answers



#region file submit and quesiton answer save
@app.post("/upload-file/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = await upload_and_save_file(current_user, file, db)
    return result

async def upload_and_save_file(current_user: User, file: UploadFile, db: Session):
    if not current_user:
        raise HTTPException(status_code=400, detail="User is not authenticated or email is missing.")

    file_extension = os.path.splitext(file.filename)[1]
    guid_file_name = f"{uuid.uuid4()}{file_extension}"

    base_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    user_directory = os.path.join(base_directory, 'files', current_user.email)

    os.makedirs(user_directory, exist_ok=True)
    file_location = os.path.join(user_directory, guid_file_name)

    with open(file_location, "wb") as f:
        f.write(await file.read())

    db_file = UploadedFile(
        userid=current_user.userid,
        original_filename=file.filename,
        saved_filename=guid_file_name,
        filepath=file_location,
        createdby=current_user.userid
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return {
        "original_filename": file.filename,
        "saved_filename": guid_file_name
    }



@app.post("/save-questions-and-answers/")
async def save_questions_and_answers(
    request: schemas.SaveQuestionsAndAnswersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # logger.debug(f"Received fileid: {request.fileid}")
    # logger.debug(f"Received question_answer_pairs: {request.question_answer_pairs}")

    try:
        # Start a transaction
        for pair in request.question_answer_pairs:
            db_question = models.Question(
                fileid=request.fileid,
                questiontext=pair.question,
                questiontype=pair.question_type,
                createdby=current_user.userid,
            )
            db.add(db_question)
            db.commit()
            db.refresh(db_question)
            
            db_answer = models.Answer(
                questionid=db_question.questionid,
                correctanswertext=pair.answer,
                istrue=True if pair.question_type == "TrueFalse" and pair.answer.lower() == "true" else False,
                createdby=current_user.userid,
            )
            db.add(db_answer)
            db.commit()

        return {"status": "Questions and answers saved successfully"}

    except Exception as e:
        # Roll back in case of error
        db.rollback()
        logger.error(f"Error saving questions and answers: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while saving the questions and answers")


@app.get("/file-question-summaries/", response_model=List[schemas.FileQuestionSummary])
def get_file_question_summaries_endpoint(db: Session = Depends(get_db)):
    return get_file_question_summaries(db)

def get_file_question_summaries(db: Session) -> List[schemas.FileQuestionSummary]:
    # Perform the query to join the File and Question tables
    summaries = db.query(
        UploadedFile.fileid.label('file_id'),
        UploadedFile.original_filename.label('original_filename'),
        func.count(Question.questionid).label('number_of_questions'),
        UploadedFile.uploaddate.label('uploaddate')
    ).join(Question, Question.fileid == UploadedFile.fileid) \
     .group_by(UploadedFile.fileid) \
     .all()

    # logger.error(f"summaries: {summaries}")
    # Convert the result to a list of Pydantic models
    return [schemas.FileQuestionSummary(
                file_id=summary.file_id,
                original_filename=summary.original_filename,
                number_of_questions=summary.number_of_questions,
                uploaddate=summary.uploaddate
                ) for summary in summaries]

#endregion



#region file wise quesitons related funciton
@app.get("/file-question-summaries/{file_id}", response_model=schemas.FileQuestionSummary)
def get_file_question_summary(file_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Perform the query to get the file summary
    summary = db.query(
        models.UploadedFile.fileid.label('file_id'),
        models.UploadedFile.original_filename.label('original_filename'),
        func.count(models.Question.questionid).label('number_of_questions'),
        models.UploadedFile.uploaddate.label('uploaddate')
    ).join(models.Question, models.Question.fileid == models.UploadedFile.fileid) \
     .filter(models.UploadedFile.fileid == file_id) \
     .group_by(models.UploadedFile.fileid) \
     .first()

    if not summary:
        raise HTTPException(status_code=404, detail="File not found")

    return schemas.FileQuestionSummary(
        file_id=summary.file_id,
        original_filename=summary.original_filename,
        number_of_questions=summary.number_of_questions,
        uploaddate=summary.uploaddate
    )

@app.get("/file-questions/{file_id}", response_model=List[schemas.QuestionAnswerPair])
def get_questions_for_file(file_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Perform the query to get the questions for the specified file
    questions = db.query(
        models.Question.questiontext.label('question'),
        models.Question.questiontype.label('question_type'),
        models.Answer.correctanswertext.label('answer')
    ).join(models.Answer, models.Answer.questionid == models.Question.questionid) \
     .filter(models.Question.fileid == file_id) \
     .all()

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for the specified file")

    return [schemas.QuestionAnswerPair(
                question=question.question,
                question_type=question.question_type,
                answer=question.answer
            ) for question in questions]


@app.get("/file-content/{file_id}", response_class=PlainTextResponse)
def get_file_content(file_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Query the file record from the database
    file_record = db.query(UploadedFile).filter(UploadedFile.fileid == file_id).first()
    # logger.error(f"file path from database : {file_record.filepath}")
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Ensure the 'filepath' is a string
    file_path = file_record.filepath

    # Check if the file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on the server")

    # Read and return the content of the file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return content



#endregion

#region test

@app.get("/file-questions-new/{file_id}", response_model=List[schemas.QuestionAnswerPairNew])
def get_questions_for_file(file_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Perform the query to get the questions for the specified file
    questions = db.query(
        models.Question.questionid.label('question_id'),  # Add question_id to the query
        models.Question.questiontext.label('question'),
        models.Question.questiontype.label('question_type'),
        models.Answer.correctanswertext.label('answer')
    ).join(models.Answer, models.Answer.questionid == models.Question.questionid) \
     .filter(models.Question.fileid == file_id) \
     .all()

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for the specified file")

    return [schemas.QuestionAnswerPairNew(
                question_id=question.question_id,  # Include question_id in the response
                question=question.question,
                question_type=question.question_type,
                answer=question.answer
            ) for question in questions]






@app.post("/submit-answers/", response_model=schemas.TestResult)
async def submit_answers(
    request: schemas.SubmitAnswersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        score = 0
        total_questions = len(request.user_answers)

        # Step 1: Create a new UserTest entry
        user_test = models.UserTest(
            userid=current_user.userid,
            fileid=request.fileid,
            createdby=current_user.userid
        )
        db.add(user_test)
        db.commit()
        db.refresh(user_test)

        # Step 2: Save each user's answer in the UserAnswer table
        for answer in request.user_answers:
            correct_answer = db.query(models.Answer).filter(models.Answer.questionid == answer.question_id).first()
            
            if correct_answer:
                if request.question_type == "TrueFalse":
                    is_true = (answer.answer.lower() == "true") if answer.answer is not None else None
                    if is_true == correct_answer.istrue:
                        score += 1

                    db_user_answer = models.UserAnswer(
                        testid=user_test.testid,
                        questionid=answer.question_id,
                        givenanswertext=None,  # No text for TrueFalse questions
                        istrue=is_true,
                        createdby=current_user.userid,
                    )
                elif request.question_type == "FillInTheBlanks":
                    if answer.answer == correct_answer.correctanswertext:
                        score += 1

                    db_user_answer = models.UserAnswer(
                        testid=user_test.testid,
                        questionid=answer.question_id,
                        givenanswertext=answer.answer,  # Store the given answer text
                        istrue=None,  # isTrue is null for FillInTheBlanks
                        createdby=current_user.userid,
                    )
                
                db.add(db_user_answer)
                db.commit()

        # Step 3: Save the result in the Result table
        result = models.Result(
            testid=user_test.testid,
            score=score,
            totalquestions=total_questions,
            correctanswers=score,
            createdby=current_user.userid,
        )
        db.add(result)
        db.commit()

        # Step 4: Return the result to the frontend
        return {
            "score": score,
            "total_questions": total_questions,
            "correct_answers": score
        }

    except SQLAlchemyError as e:
        db.rollback()  # Roll back the transaction if an error occurs
        logger.error(f"Error during submitting answers: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while submitting your answers. Please try again.")



#endregion