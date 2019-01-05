import os

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, session,render_template,request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import flash

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
        return render_template("index_project1.html" )
    book_search=request.form.get("book_search")
    query=request.form.get("query")
    if book_search=="year":
        bookresult=db.execute("SELECT * FROM books WHERE year=:query",{"query":query}).fetchall()
    else:
        bookresult = db.execute("SELECT * FROM books WHERE UPPER(" + book_search + ") = :query ORDER BY title",
                               {"query": query.upper()}).fetchall()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)