from fastapi import FastAPI, File, UploadFile, Request, HTTPException,Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List, Dict
import spacy
from transformers import pipeline
import uuid

app = FastAPI()

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

@app.post("/", response_class=HTMLResponse)
async def handle_file_upload(request: Request, file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode('utf-8')
    questions, answers = generate_questions(text)
    return templates.TemplateResponse("index.html", {"request": request, "questions": questions, "answers": answers})

def generate_questions(text):
    doc = nlp(text)
    questions = []
    correct_answers = {}
    count = 0

    for sent in doc.sents:
        if count >= 10:
            break
        paraphrased = paraphrase_sentence(sent.text)
        if not paraphrased:  # Skip if paraphrasing fails
            continue

        # Find the first significant named entity to blank out
        paraphrased_doc = nlp(paraphrased)
        entities = [ent for ent in paraphrased_doc.ents if ent.label_ in {'PERSON', 'ORG', 'GPE', 'LOC', 'DATE', 'EVENT'}]
        if not entities:
            continue  # Skip if no suitable entity is found

        first_entity = entities[0]  # Focus on the first entity found
        modified_text = paraphrased.replace(first_entity.text, "__input__", 1)  # Replace first occurrence only

        question_id = str(uuid.uuid4())
        questions.append({
            'id': question_id,
            'question': modified_text,
            'entity': first_entity.text
        })
        correct_answers[question_id] = first_entity.text  # Store correct answer
        count += 1

    return questions, correct_answers


def paraphrase_sentence(sentence):
    try:
        paraphrase_prompt = f"paraphrase: {sentence} </s>"
        paraphrased_results = paraphraser(paraphrase_prompt, max_length=100)
        return paraphrased_results[0]['generated_text'] if paraphrased_results else None
    except Exception as e:
        print(f"An error occurred during paraphrasing: {e}")
        return None

@app.post("/submit-answers", response_class=HTMLResponse)
async def submit_answers(request: Request,
                         session_id: str = Form(...),
                         answers: List[str] = Form(...),
                         question_ids: List[str] = Form(...)):
    # Debugging: print incoming data
    print(f"Session ID: {session_id}, Answers: {answers}, Question IDs: {question_ids}")

    # Check if the session ID exists
    if session_id not in questions_store:
        raise HTTPException(status_code=404, detail="Session not found")

    correct_answers = questions_store[session_id]
    score = 0
    for question_id, answer in zip(question_ids, answers):
        if question_id in correct_answers:
            correct_answer = correct_answers[question_id]
            if answer.strip().lower() == correct_answer.strip().lower():
                score += 1

    return templates.TemplateResponse("score.html", {"request": request, "score": score, "total": len(question_ids)})



