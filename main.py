from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import os
from openai import OpenAI 
from dotenv import load_dotenv

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
def recommend_books(user_prompt: str):
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        
        # fetching data
        cursor.execute("SELECT * FROM books WHERE popularity_score < 50")
        book_pool = cursor.fetchall()

        # passing user's vibe and booklist to the llm
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a niche book agent. Recommend books based on the user's vibe, specifically avoiding mainstream bestsellers."},
                {"role": "user", "content": f"User wants: {user_prompt}. Choose from this list: {book_pool}"}
            ]
        )
        
        return {"recommendation": response.choices[0].message.content}
    
    finally:
        connection.close()

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