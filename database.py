import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    conn = psycopg2.connect(DATABASE_URL)
else:
    conn = psycopg2.connect(
        host="localhost",
        database="bookbasket",
        user="postgres",
        password="admin@123"
    )

cur = conn.cursor()

print("Connected to PostgreSQL!")