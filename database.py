import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="bookbasket",
    user="postgres",
    password="admin@123"
)

cur = conn.cursor()

print("Connected to BookBasket Database Successfully!")