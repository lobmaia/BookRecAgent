# Book Reccomendation Agent

A RAG-based recommendation engine that utilizes GPT-3.5 and a MySQL database to match abstract user "vibes" to a library of 10,000+ books. It implements a logarithmic popularity normalization algorithm to eliminate best-seller bias and surface niche "hidden gems."

## Key Features

* **RAG Architecture:** Injects filtered SQL metadata into the LLM context window, allowing for precise recommendations grounded in a private, local dataset.
* **Logarithmic Scaling:** Implements a NumPy-based $\log_{10}$ normalization of ratings_count to equalize the influence of niche vs. mainstream titles in search results.
* **Intelligent Sequel Filtering:** Uses Regex-based title analysis to identify and remove series sequels (i.e., "#2", "#3"), prioritizing standalone entry points for new readers.
* **Secure API Design:** Features a FastAPI backend with parameterized SQL queries to prevent injection attacks and ensure consistent JSON structured outputs.
  
## Tech Stack

* **Core:** Python 3.10+, FastAPI
* **Database:** MySQL
* **AI:** OpenAI API (GPT-3.5-Turbo)
* **Data Science:** Pandas, NumPy
* **Testing:** Postman

## Project Structure

```text
BookRecAgent/
├── .env                # API keys and DB credentials 
├── .gitignore          # Prevents sensitive files from being tracked
├── books.csv           # Raw Kaggle dataset
├── data_ingestion.py   # Data pipeline (Log-scaling and cleaning)
├── main.py             # FastAPI endpoints and RAG logic
