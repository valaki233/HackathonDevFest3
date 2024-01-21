
import score, os
import flask
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import re
import mysql.connector
from datetime import date

app = Flask(__name__)
app.debug = True

app.config["SESSION_TYPE"] = "filesystem"
Session(app)

userdb = mysql.connector.connect(
    host=os.getenv('sql_host'),
    user=os.getenv('sql_username'),
    password=os.getenv('sql_password'),
    database=os.getenv('sql_db'),
    port=int(os.getenv('sql_port'))
)
returned_data = []

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def login_required(f):
    @wraps(f)

    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        else:
            pass
        return f(*args, **kwargs)
    return decorated_function

@app.route("/uploads/<user_id>/<file_name>", methods=['GET', 'POST'])
@login_required
def download_file(user_id, file_name):
    if(int(user_id) != session["user_id"]):
        return render_template("/download.html", msg="You have no access to that file", inplst="", id="")
    return flask.send_file("./uploads/" + user_id + "/" + file_name, as_attachment=True)
    

@app.template_global(name='zip')
def _zip(*args, **kwargs): #to not overwrite builtin zip in globals
    return __builtins__.zip(*args, **kwargs)

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    datas = []
    txt = ''
    try:
        with open(f"""./user_data/{session['user_id']}/data.txt""") as f:
            datas = f.readlines()
    except:
        txt = 'No Notes Available'

    data_matrix = []
    for data in datas: 
        d = data.split(":")
        data_matrix.append(d) 

    for a in data_matrix:
        a[3] = a[3].replace('\n', '')
    print(data_matrix)
    datastr = str(data_matrix).replace("[", "").replace("],", ";").replace("'", "").replace("]]", "")
    return render_template('/index.html', data=datastr, txt=txt)


Scorer = score.Score()
ALLOWED_TYPES = [".txt",".md"]
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files["file"]
        allowed = 0
        for e in ALLOWED_TYPES:
            if file.filename.endswith(e):
                allowed = 1
        if not allowed:
            return render_template('/upload.html', data="File type not allowed, only .txt .docx and .md files are suitable")
        #scoring
        if not os.path.exists("./uploads/" + str(session["user_id"])):
            os.mkdir("./uploads/" + str(session["user_id"]))
        if file.filename in os.listdir("./uploads/" + str(session["user_id"])):
            os.remove("./uploads/" + str(session["user_id"]) + "/" + file.filename)
        file.save("./uploads/" + str(session["user_id"]) + "/" + file.filename)
        tscore = str(Scorer.get_score(request.form.get("class"), file.filename, session["user_id"])[2])
        if not os.path.exists("./user_data/" + str(session["user_id"])):
            os.mkdir("./user_data/" + str(session["user_id"]))
            open("./user_data/" + str(session["user_id"]) + "/data.txt", "x")
        data = open("./user_data/" + str(session["user_id"]) + "/data.txt", "a")
        data.write(request.form.get("class") + ":" + file.filename + ":" + tscore + ":" + str(date.today()) + "\n")
        return render_template('/upload.html', data=tscore)
    else:
        return render_template('/upload.html')



################################login##################################

@app.route("/login", methods=["GET", "POST"])
def login():

    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", data="Make sure you type in your username.")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", data="Make sure you type in your password.")

        # Query database for username
        cursor = userdb.cursor()
        cursor.execute(f'SELECT * FROM users WHERE username="{request.form.get("username")}" ')
        rows = cursor.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][3], request.form.get("password")):
            return render_template("login.html", data="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/download")
@login_required
def download():
    #Check notes, download
    if os.path.exists("./uploads/" + str(session["user_id"])):
        lst = os.listdir("./uploads/" + str(session["user_id"]))
        print(lst)
        return render_template("download.html", data=str(lst).replace("[", "").replace("]", "").replace("'", "").replace(",", ";").replace(" ", ""), id=str(session["user_id"]))
    else:
        return render_template("download.html", data="No files available")
    # Redirect user to login form

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        pw_two = request.form.get("confirmation")

        cursor = userdb.cursor()
        cursor.execute("SELECT username FROM users;")
        usernames = cursor.fetchall()
        print(usernames)

        cursor = userdb.cursor()
        cursor.execute("SELECT email FROM users;")
        emails = cursor.fetchall()
        print(username)
        #print(usernames[0]['username'])
        if username == '' or password == '' or pw_two == '' or email == '':
            return render_template("register.html", data="you need to fill out all of the fields!")
        if is_valid_email(email) == 0:
            return render_template("register.html", data="invalid email please provide a real email address")

        i=0
        while i<len(usernames):
            if usernames[i][0].lower() == username.lower():
                return render_template("register.html", data="Username already in use!")
            elif emails[i][0] == email:
                return render_template("register.html", data="Email already in use!")
            i+=1

        if password == pw_two:
            if is_valid_password(password) == 1:
                hash = generate_password_hash(password)
                print(hash)
                cursor = userdb.cursor()
                cursor.execute(f'INSERT INTO users (username, email, pwdhash) VALUES("{username}", "{email}", "{hash}");')
                userdb.commit()
                cursor = userdb.cursor()
                cursor.execute(f'SELECT id FROM users WHERE username = "{username}"')
                session_id = cursor.fetchall()
                session["user_id"] = session_id[0][0]
                
            else:
                return "Password must be at least 8 characters long and contain at least one number and one uppercase letter"

            return redirect("/")

        else:
            return render_template("register.html", data="passwords don't mach!")

    else:
        return render_template("register.html")


def is_valid_password(password):
    if len(password) < 8:
        return 4
    if not re.search(r'[A-Z]', password):
        return 2
    if not re.search(r'\d', password):
        return 3
    return 1

def is_valid_email(email):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return 1
    else:
        return 0