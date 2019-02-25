import os

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, session,render_template,request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import flash
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('index_project1.html')
    else:
        return render_template("home.html")
 
@app.route('/signup', methods=['GET','POST'])
def do_admin_login():
    if request.method=="POST":
        email=request.form.get("email_address")
        if db.execute("SELECT ID FROM users WHERE email=:email ",{"email":email}).fetchone() is not None: 
            return render_template("index_project1.html", error_message="user exit . try another")
        password=request.form.get("pwd")
        db.execute("INSERT INTO users (email,password) VALUES(:email,:password)",{"email":email,"password":generate_password_hash(password)})
        db.commit()    
        return home()
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()




@app.route("/login", methods=["GET","POST"])    
def login():
    if request.method=="POST":
        email=request.form.get("email_address")
        user=db.execute("SELECT ID,password FROM users WHERE email=:email ",{"email":email}).fetchone()
        if user is None: 
            return render_template("index_project1.html", error_message="user doesn't exit")
        password=request.form.get("pwd")
        if not check_password_hash(user.password,password):
            return render_template("index_project1.html", error_message="password is wrong")
        session["user_email"] = email
        session["user_id"] = user.id
        session['logged_in'] = True
    if request.method == "GET" and "user_email" not in session:
        return render_template("index_project1.html", error_message="Please Login First")
    return home()

@app.route("/bookresult", methods=["POST"])        
def bookresult():
    if session['logged_in'] is False:
        return render_template("index_project1.html")
    book_search = request.form.get("book_search")
    query = request.form.get("query")
    if book_search == "year":
        bookresult = db.execute("SELECT * FROM books WHERE year = :query", {"query": query}).fetchall()
    else:
        bookresult = db.execute("SELECT * FROM books WHERE UPPER(" + book_search + ") = :query ORDER BY title",{"query": query.upper()}).fetchall()

    # Is whole of the info i.e. ISBN, title matches...
    if len(bookresult):
        return render_template("bookresult.html", bookresult=bookresult, user_email=session["user_email"])

    elif book_search != "year":
        error_message = "We couldn't find the books you searched for."
        bookresult = db.execute("SELECT * FROM books WHERE UPPER(" + book_search + ") LIKE :query ORDER BY title",{"query": "%" + query.upper() + "%"}).fetchall()
        if not len(bookresult):
            return render_template("error.html", error_message=error_message)
        message = "You might be searching for:"
        return render_template("bookresult.html", error_message=error_message, bookresult=bookresult, message=message,user_email=session["user_email"])
    else:
        return render_template("error.html", error_message="We didn't find any book with the year you typed."" Please check for errors and try again.")


@app.route("/bookpage/<int:book_id>", methods=["GET", "POST"])
def bookpage(book_id):
    if session['logged_in'] is False:
        return render_template("index_project1.html")
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", error_message="There is no book with that Book id")

    if request.method == "POST":
        user_id = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        if db.execute("SELECT * FROM reviews WHERE user_id=:user_id , book_id=:book_id",{"user_id": user_id, "book_id": book_id}).fetchone() is None:
            db.execute("INSERT INTO reviews (user_id,book_id,rating,comment) VALUES (:user_id, :book_id, :rating, :comment)",{"user_id": user_id, "book_id": book_id, "rating": rating, "comment": comment })
        else:
            db.execute("UPDATE reviews SET comment = :comment, rating = :rating WHERE user_id = :user_id AND book_id = :book_id",{"comment": comment, "rating": rating, "user_id": user_id, "book_id": book_id})
        db.commit()
    
    res = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key": "od8Y5FsZdfQ0V5RpYYm8Q", "isbns": book.isbn}).json()["books"][0]
    ratings_count = res["ratings_count"]
    average_rating = res["average_rating"]
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()
    users = []
    for review in reviews:
        email = db.execute("SELECT email FROM users WHERE id = :user_id", {"user_id": review.user_id}).fetchone().email
        users.append((email, review))

    return render_template("bookpage.html", book=book, users=users,ratings_count=ratings_count, average_rating=average_rating, user_email=session["user_email"])
                
# Page for the website's API
@app.route("/api/<ISBN>", methods=["GET"])
def api(ISBN):
    book = db.execute("SELECT * FROM books WHERE isbn = :ISBN", {"ISBN": ISBN}).fetchone()
    if book is None:
        return render_template("error.html", error_message="We got an invalid ISBN. ""Please check for the errors and try again.")
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()
    count = 0
    rating = 0
    for review in reviews:
        count += 1
        rating += review.rating
    if count:
        average_rating = rating / count
    else:
        average_rating = 0

    return jsonify(
        title=book.title,
        author=book.author,
        year=book.year,
        isbn=book.isbn,
        review_count=count,
        average_score=average_rating
    )


#if __name__ == "__main__":
    app.run(debug=True)
