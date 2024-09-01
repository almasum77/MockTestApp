import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app, get_db
from src.database.models import Base, UploadedFile, Question, Answer
from unittest.mock import patch, MagicMock

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="module")
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@patch("src.main.upload_and_save_file", MagicMock(return_value={"saved_filename": "mockfile.txt"}))
@patch("src.main.open", MagicMock(return_value="This is a test document for question generation."))
def test_generate_questions(client, test_db):
    file_mock = MagicMock(spec=UploadFile)
    file_mock.filename = "mockfile.txt"
    
    response = client.post("/generate-questions/", 
        params={
            "question_size": 5,
            "question_types": ["FillInTheBlanks", "TrueFalse"]
        },
        files={"file": ("filename", file_mock, "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert "session_id" in data
    assert len(data["question_answer_pairs"]) > 0

def test_save_questions_and_answers(client, test_db):
    file = UploadedFile(
        userid=1,
        original_filename="mockfile.txt",
        saved_filename="mockfile.txt",
        filepath="files/mockfile.txt"
    )
    test_db.add(file)
    test_db.commit()

    response = client.post("/save-questions-and-answers/", json={
        "fileid": file.fileid,
        "question_answer_pairs": [
            {
                "question": "What is the capital of France?",
                "question_type": "FillInTheBlanks",
                "answer": "Paris"
            },
            {
                "question": "Paris is the capital of France.",
                "question_type": "TrueFalse",
                "answer": "True"
            }
        ]
    })
    assert response.status_code == 200
    assert response.json() == {"status": "Questions and answers saved successfully"}
