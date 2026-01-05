import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
import numpy as np
import re

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def ingest_books(csv_path):
    # loading data
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python')
    df.columns = df.columns.str.strip()
    
    df = df[~df['title'].str.contains(r'#([2-9]|\d{2,})', regex=True)]
    df['log_ratings'] = np.log10(df['ratings_count'] + 1)

    # calculating popularity score 
    # 1 is very niche and 100 is very mainstream 
    max_log = df['log_ratings'].max()
    df['popularity_score'] = (df['log_ratings'] / max_log * 100).astype(int)

    # clean data
    df = df.dropna(subset=['title', 'authors'])
    df = df.sort_values('ratings_count', ascending=False).drop_duplicates('title')

    books_to_insert = []
    for _, row in df.iterrows():
        clean_author = str(row['authors']).replace('/', ', ')
        placeholder_desc = f"A book by {row['authors']}. (Note to AI: Use your internal knowledge for this title)."
        
        books_to_insert.append((
            str(row['title'])[:255],
            str(row['authors'])[:255],
            placeholder_desc,
            "fiction",  
            int(row['popularity_score'])
        ))

    # bulk upload
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()
    
    query = "INSERT INTO books (title, author, description, tropes, popularity_score) VALUES (%s, %s, %s, %s, %s)"
    
    print(f"Uploading {len(books_to_insert)} books...")
    try:
        for i in range(0, len(books_to_insert), 1000):
            batch = books_to_insert[i:i+1000]
            cursor.executemany(query, batch)
            conn.commit()
            print(f"Batch {i//1000 + 1} complete...")
    finally:
        cursor.close()
        conn.close()
        print("Success!")

if __name__ == "__main__":
    ingest_books("books.csv")