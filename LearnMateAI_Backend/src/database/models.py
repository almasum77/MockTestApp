from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'  # This should be lowercase

    userid = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    firstname = Column(String(50), nullable=True)
    lastname = Column(String(50), nullable=True)
    hashedpassword = Column(String(255), nullable=False)
    createddate = Column(DateTime(timezone=True), server_default=func.now())
    createdby = Column(Integer, nullable=True)

    # Relationships
    files = relationship('UploadedFile', back_populates='user')
    tests = relationship('UserTest', back_populates='user')



class UploadedFile(Base):
    __tablename__ = 'files'

    fileid = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, ForeignKey('users.userid'))
    original_filename = Column(String(255), nullable=False)
    saved_filename = Column(String(255), nullable=False)
    filepath = Column(String(255), nullable=True)
    uploaddate = Column(DateTime(timezone=True), server_default=func.now())
    createddate = Column(DateTime(timezone=True), server_default=func.now())
    createdby = Column(Integer, nullable=True)

    # Relationships
    user = relationship('User', back_populates='files')
    questions = relationship('Question', back_populates='file')
    tests = relationship('UserTest', back_populates='file')



class Question(Base):
    __tablename__ = 'questions'

    questionid = Column(Integer, primary_key=True, index=True)
    fileid = Column(Integer, ForeignKey('files.fileid'))  # Foreign key in lowercase
    questiontext = Column(Text, nullable=False)
    questiontype = Column(String(20), nullable=False)  # 'FillInTheBlanks' or 'TrueFalse'
    createddate = Column(DateTime(timezone=True), server_default=func.now())
    createdby = Column(Integer, nullable=True)

    # Relationships
    file = relationship('UploadedFile', back_populates='questions')
    answers = relationship('Answer', back_populates='question')
    user_answers = relationship('UserAnswer', back_populates='question')



class Answer(Base):
    __tablename__ = 'answers'

    answerid = Column(Integer, primary_key=True, index=True)
    questionid = Column(Integer, ForeignKey('questions.questionid'))  # Foreign key in lowercase
    correctanswertext = Column(Text, nullable=True)
    istrue = Column(Boolean, nullable=True)  # For True/False questions
    createddate = Column(DateTime(timezone=True), server_default=func.now())
    createdby = Column(Integer, nullable=True)

    # Relationships
    question = relationship('Question', back_populates='answers')



class UserTest(Base):
    __tablename__ = 'user_tests'

    testid = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, ForeignKey('users.userid'))  # Foreign key in lowercase
    fileid = Column(Integer, ForeignKey('files.fileid'))  # Foreign key in lowercase
    testno = Column(String(50), unique=True, nullable=False)
    testdate = Column(DateTime(timezone=True), server_default=func.now())
    createddate = Column(DateTime(timezone=True), server_default=func.now())
    createdby = Column(Integer, nullable=True)

    # Relationships
    user = relationship('User', back_populates='tests')
    file = relationship('UploadedFile', back_populates='tests')
    user_answers = relationship('UserAnswer', back_populates='test')
    results = relationship('Result', back_populates='test')



class UserAnswer(Base):
    __tablename__ = 'user_answers'

    useranswerid = Column(Integer, primary_key=True, index=True)
    testid = Column(Integer, ForeignKey('user_tests.testid'))  # Foreign key in lowercase
    questionid = Column(Integer, ForeignKey('questions.questionid'))  # Foreign key in lowercase
    givenanswertext = Column(Text, nullable=True)
    istrue = Column(Boolean, nullable=True)
    createddate = Column(DateTime(timezone=True), server_default=func.now())
    createdby = Column(Integer, nullable=True)

    # Relationships
    test = relationship('UserTest', back_populates='user_answers')
    question = relationship('Question', back_populates='user_answers')



class Result(Base):
    __tablename__ = 'results'

    resultid = Column(Integer, primary_key=True, index=True)
    testid = Column(Integer, ForeignKey('user_tests.testid'))  # Foreign key in lowercase
    score = Column(Integer, nullable=True)
    totalquestions = Column(Integer, nullable=True)
    correctanswers = Column(Integer, nullable=True)
    createddate = Column(DateTime(timezone=True), server_default=func.now())
    createdby = Column(Integer, nullable=True)

    # Relationships
    test = relationship('UserTest', back_populates='results')




