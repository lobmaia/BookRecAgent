from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import os
from openai import OpenAI 

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
    cursor = connection.cursor()

    query = """
    INSERT INTO book (title, author, description, tropes, popularity_score)
    VALUES (%s, %s, %s, %s, %s, %i)
    """
    values = (book.title, book.author, book.description, book.tropes, book.popularity_score)

    cursor.execute(query, values)
    # saves changes to the database
    connection.commit()

    # closing both the connection and the cursor to free up memory
    cursor.close()
    connection.close()
    return {"message": "Book added to library"}