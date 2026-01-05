from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import os
from openai import OpenAI 
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# data model
class Book(BaseModel):
    title: str
    author: str
    description: str
    tropes: str
    popularity_score: int  

# database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# agent logicpython -m venv <directory>
@app.post("/recommend")
def recommend_books(user_prompt: str, genre: str = None):
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        
        genre_filter = f"AND (tropes LIKE '%{genre}%' OR description LIKE '%{genre}%')" if genre else ""

        query = """
            SELECT title, author, description, tropes 
            FROM books 
            WHERE popularity_score BETWEEN 35 AND 70
        """
        params = []
        
        # adding genre filter
        if genre:
            query += " AND (tropes LIKE %s OR description LIKE %s)"
            genre_param = f"%{genre}%"
            params.extend([genre_param, genre_param])
        
        query += " ORDER BY RAND() LIMIT 50"

        cursor.execute(query)
        book_pool = cursor.fetchall()

        if not book_pool:
            raise HTTPException(status_code=404, detail="No niche books found. Did you run the ingestion script?")

        books_string = json.dumps(book_pool)

        # passing user's vibe and sample pool to the LLM
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": """You are a professional book curator. You must return your response in strictly valid JSON format. The JSON should have these keys: 'book_title', 'author', 'reasoning', and 'vibe_match_score' (1-100). Your tone should be poetic but concise.
"""
                },
                {
                    "role": "user", 
                    "content": f"User's Vibe: {user_prompt}. Look through these titles. Even if the description is brief, use your knowledge of these famous works to find the best match: {books_string}"
                }
            ]
        )
        
        return {"recommendation": response.choices[0].message.content}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

    raw_content = response.choices[0].message.content
        
    try:
        structured_data = json.loads(raw_content)
        return {"recommendation": structured_data}
    except:
        return {"recommendation": raw_content}

# routes
@app.post("/books/")
def add_book(book: Book):
    connection = get_db_connection()
    
    try:
        cursor = connection.cursor()

        query = """
        INSERT INTO books (title, author, description, tropes, popularity_score)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (book.title, book.author, book.description, book.tropes, book.popularity_score)

        cursor.execute(query, values)
        connection.commit()
        return {"message": "Book added to library"}
    
    finally:
        cursor.close()
        connection.close()

# only testing
@app.post("/seed")
def seed_books():
    # example books
    niche_books = [
        ("Circe", "Madeline Miller", "A retelling of the goddess Circe's life.", "mythology, feminism", 45),
        ("Piranesi", "Susanna Clarke", "A man lives in a labyrinthine house of statues.", "surreal, mystery", 35),
        ("The Night Circus", "Erin Morgenstern", "A magical competition between two young illusionists.", "atmospheric, romance", 48),
        ("Convenience Store Woman", "Sayaka Murata", "A woman finds comfort in the rigidity of store work.", "quirky, social-commentary", 20)
    ]
    
    connection = get_db_connection()

    try:
        cursor = connection.cursor()
        query = "INSERT INTO books (title, author, description, tropes, popularity_score) VALUES (%s, %s, %s, %s, %s)"
        cursor.executemany(query, niche_books)
        connection.commit()
        return {"status": "success", "message": f"Added {cursor.rowcount} books"}
    
    finally:
        connection.close()