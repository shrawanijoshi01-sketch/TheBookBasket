from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Request, Form
from typing import Optional
from database import conn, cur

import os

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "bookbasket123")
)

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


# ---------------- REGISTER PAGE ---------------- #

@app.get("/", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


# ---------------- REGISTER ---------------- #

@app.post("/register")
def register(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    query = """
    INSERT INTO users (full_name, email, password)
    VALUES (%s, %s, %s)
    """

    cur.execute(query, (full_name, email, password))
    conn.commit()

    return RedirectResponse(url="/login", status_code=303)


# ---------------- LOGIN PAGE ---------------- #

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

from typing import Optional

@app.get("/books", response_class=HTMLResponse)
def books_page(
    request: Request,
    genre: Optional[str] = None,
    search: Optional[str] = None
):

    if search:
        cur.execute("""
            SELECT * FROM books
            WHERE
                title ILIKE %s
                OR author ILIKE %s
                OR genre ILIKE %s
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))

    elif genre:
        cur.execute("""
            SELECT * FROM books
            WHERE genre = %s
        """, (genre,))

    else:
        cur.execute("""
            SELECT * FROM books
        """)

    books = cur.fetchall()

    return templates.TemplateResponse(
        request=request,
        name="books.html",
        context={
            "books": books,
            "search": search,
            "selected_genre": genre
        }
    )
    


# 👇 ADD THE NEW ROUTE HERE

@app.get("/book/{book_id}", response_class=HTMLResponse)
def book_details(request: Request, book_id: int):

    # Get the selected book
    cur.execute(
        """
        SELECT * FROM books
        WHERE id = %s
        """,
        (book_id,)
    )

    book = cur.fetchone()

    if not book:
        return HTMLResponse("<h2>Book not found!</h2>", status_code=404)

    genre = book[3]

    # Get recommendations
    cur.execute(
        """
        SELECT * FROM books
        WHERE genre = %s
        AND id != %s
        LIMIT 4
        """,
        (genre, book_id)
    )

    recommendations = cur.fetchall()

    return templates.TemplateResponse(
        request=request,
        name="book_details.html",
        context={
            "book": book,
            "recommendations": recommendations
        }
    )



# ---------------- LOGIN ---------------- #

@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):

    query = """
    SELECT * FROM users
    WHERE email=%s AND password=%s
    """

    cur.execute(query, (email, password))

    user = cur.fetchone()

    if user:

        request.session["user_id"] = user[0]
        request.session["user_name"] = user[1]

        return RedirectResponse(url="/home", status_code=303)

    return HTMLResponse("""
        <h2>❌ Invalid Email or Password</h2>
        <a href="/login">Try Again</a>
    """)


# ---------------- HOME PAGE ---------------- #

@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html"
    )

from typing import Optional

@app.get("/logout")
def logout(request: Request):

    request.session.clear()

    return RedirectResponse("/", status_code=303)
@app.post("/add_to_cart/{book_id}")
def add_to_cart(request: Request, book_id: int):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    # Check if book already exists in cart
    cur.execute(
        """
        SELECT * FROM cart
        WHERE user_id=%s AND book_id=%s
        """,
        (user_id, book_id)
    )

    item = cur.fetchone()

    if item:
        # Increase quantity
        cur.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE user_id=%s AND book_id=%s
            """,
            (user_id, book_id)
        )
    else:
        # Insert new book
        cur.execute(
            """
            INSERT INTO cart(user_id, book_id, quantity)
            VALUES(%s,%s,%s)
            """,
            (user_id, book_id, 1)
        )

    conn.commit()

    return RedirectResponse("/books", status_code=303)
@app.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    cur.execute("""
        SELECT
            books.id,
            books.title,
            books.author,
            books.price,
            books.image,
            cart.quantity
        FROM cart
        JOIN books
        ON cart.book_id = books.id
        WHERE cart.user_id = %s
    """, (user_id,))

    cart_items = cur.fetchall()

    total = 0

    for item in cart_items:
        total += item[3] * item[5]

    return templates.TemplateResponse(
        request=request,
        name="cart.html",
        context={
            "cart_items": cart_items,
            "total": total
        }
    )
@app.get("/checkout", response_class=HTMLResponse)
def checkout_page(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    cur.execute("""
        SELECT
            books.price,
            cart.quantity
        FROM cart
        JOIN books
        ON cart.book_id = books.id
        WHERE cart.user_id = %s
    """, (user_id,))

    items = cur.fetchall()

    total = 0

    for item in items:
        total += item[0] * item[1]

    return templates.TemplateResponse(
        request=request,
        name="checkout.html",
        context={
            "total": total
        }
    )
@app.post("/place_order")
def place_order(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    payment: str = Form(...)
):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    # Calculate total
    cur.execute("""
        SELECT books.price, cart.quantity
        FROM cart
        JOIN books
        ON cart.book_id = books.id
        WHERE cart.user_id = %s
    """, (user_id,))

    items = cur.fetchall()

    total = 0

    for item in items:
        total += item[0] * item[1]

    # Save order
    cur.execute("""
        INSERT INTO orders
        (user_id, customer_name, phone, address, payment_method, total_amount)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        name,
        phone,
        address,
        payment,
        total
    ))
    conn.commit()

    return RedirectResponse("/order_success", status_code=303)

@app.get("/order_success", response_class=HTMLResponse)
def order_success(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="success.html"
    )
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin.html"
    )

@app.get("/admin/books", response_class=HTMLResponse)
def admin_books(request: Request):

    cur.execute("""
        SELECT * FROM books
        ORDER BY id
    """)

    books = cur.fetchall()

    return templates.TemplateResponse(
        request=request,
        name="admin_books.html",
        context={
            "books": books
        }
    )
@app.get("/admin/add_book", response_class=HTMLResponse)
def add_book_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="add_book.html"
    )
@app.post("/admin/add_book")
def add_book(
    title: str = Form(...),
    author: str = Form(...),
    genre: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    description: str = Form(...),
    image: str = Form(...)
):

    cur.execute("""
        INSERT INTO books
        (title, author, genre, price, stock, description, image)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        title,
        author,
        genre,
        price,
        stock,
        description,
        image
    ))

    conn.commit()

    return RedirectResponse("/admin/books", status_code=303)

@app.get("/admin/orders", response_class=HTMLResponse)
def admin_orders(request: Request):

    cur.execute("""
        SELECT
            id,
            customer_name,
            phone,
            address,
            payment_method,
            total_amount,
            order_date
        FROM orders
        ORDER BY id DESC
    """)

    orders = cur.fetchall()

    return templates.TemplateResponse(
    "admin_orders.html",
    {
        "request": request,
        "orders": orders
    }
)
    
@app.get("/admin/edit/{book_id}", response_class=HTMLResponse)
def edit_book(request: Request, book_id: int):

    cur.execute("""
        SELECT *
        FROM books
        WHERE id = %s
    """, (book_id,))

    book = cur.fetchone()

    return templates.TemplateResponse(
        "edit_book.html",
        {
            "request": request,
            "book": book
        }
    )
    
@app.post("/admin/update/{book_id}")
def update_book(
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    genre: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    description: str = Form(...),
    image: str = Form(...)
):

    cur.execute("""
        UPDATE books
        SET
            title=%s,
            author=%s,
            genre=%s,
            price=%s,
            stock=%s,
            description=%s,
            image=%s
        WHERE id=%s
    """,(
        title,
        author,
        genre,
        price,
        stock,
        description,
        image,
        book_id
    ))

    conn.commit()

    return RedirectResponse("/admin/books",status_code=303)

@app.get("/admin/delete/{book_id}")
def delete_book(book_id: int):

    cur.execute("""
        DELETE FROM books
        WHERE id = %s
    """, (book_id,))

    conn.commit()

    return RedirectResponse(
        url="/admin/books",
        status_code=303
    )
    