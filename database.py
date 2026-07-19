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

# ---------------- CREATE TABLES IF NOT EXISTS ---------------- #

cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        genre VARCHAR(255),
        price NUMERIC(10, 2) NOT NULL,
        stock INTEGER DEFAULT 0,
        description TEXT,
        image VARCHAR(500)
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        quantity INTEGER NOT NULL DEFAULT 1
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        customer_name VARCHAR(255) NOT NULL,
        phone VARCHAR(50) NOT NULL,
        address TEXT NOT NULL,
        payment_method VARCHAR(100) NOT NULL,
        total_amount NUMERIC(10, 2) NOT NULL,
        order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()

print("Database tables verified/created successfully!")