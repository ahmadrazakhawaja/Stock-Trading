import os

from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    prices=[]
    a=[]
    stocks=db.execute("SELECT stock FROM transactions WHERE user_id=:user_id", user_id=session["user_id"])
    zo=len(stocks)
    for x in range(zo):
        print(stocks[x]["stock"])
        s=lookup(stocks[x]["stock"])
        prices.append(s.get("price"))
    shares=db.execute("SELECT shares FROM transactions WHERE user_id=:user_id",user_id=session["user_id"])
    f=len(prices)
    m=0
    yo=len(shares)
    for l in range(yo):
        y=shares[l]["shares"]*prices[m]
        a.append(y)
        m=m+1
    u=0
    for b in range(len(a)):
        u+=a[b]

    current=db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
    u=u+current[0]["cash"]
    return render_template("index.html",stocks1=stocks,shares1=shares,prices1=prices,a1=a,u1=u,current1=current[0]["cash"])




@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    if request.method =="POST":
        if not request.form.get("symbol"):
            return apology("quote field is empty",403)
        else:
            a=request.form.get("symbol")
            quote=lookup(a)
            if not quote:
                return apology("stock not found",400)
            else:
                j=quote.get("price")
                s=session["user_id"]
                result=db.execute("SELECT cash FROM users WHERE  id=:id", id=s)
                print(result[0]["cash"])
                v=(request.form.get("shares"))
                if v.isdigit()==False:
                    return apology("wrong shares given",400)
                v=int(request.form.get("shares"))
                if v<=0:
                    return apology("wrong input",400)
                else:
                    if v*j<result[0]["cash"]:
                         print(v*j)
                         w=result[0]["cash"]-(v*j)
                         db.execute("UPDATE users SET cash=:cash WHERE id=:id", cash=w, id=s)
                         db.execute("INSERT INTO transactions (user_id,stock,shares) VALUES(:user_id,:stock,:shares)", user_id=s,stock=request.form.get("symbol"),shares=v )
                         db.execute("INSERT INTO history (user_id,transactionx,stock,price,shares,dateandtime) VALUES(:user_id,:transactionx,:stock,:price,:shares,:dateandtime)",user_id=session["user_id"],transactionx="purchased",stock=request.form.get("symbol"),price=j,shares=v,dateandtime=dt_string)
                         return redirect("/")
                    else:
                         return apology("low cash",403)




    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    a=request.args.get("username")
    print(a)
    print("hello")
    if len(a)>=1:
        result=db.execute("SELECT username FROM users",)
        s=len(result)
        for x in range(s):
            if(a==result[x]["username"]):
                return jsonify(False)
        return jsonify(True)
    else:
        return apology("username lenght issue",403)


@app.route("/history")
@login_required
def history():
    result=db.execute("SELECT * FROM history WHERE user_id=:user_id",user_id=session["user_id"])
    if not result:
        return apology("no history",403)
    else:
        return render_template("history.html",result1=result)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("quote field is empty",400)
        else:
            a=request.form.get("symbol")
            quote=lookup(a)
            if not quote:
                return apology("quote not found",400)
            else:
                redirect("/quoted")
                f=quote.get("name")
                j=quote.get("price")
                m=quote.get("symbol")
                return render_template("quoted.html",name=f,price=j,quote=m)
    else:
        return render_template("quote.html")




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method=="POST":
        if not request.form.get("username"):
            return apology("Username is empty",400)
        elif(not request.form.get("password") or not request.form.get("confirmation")):
            return apology("password field is empty",400)
        elif(request.form.get("password") != request.form.get("confirmation")):
            return apology("password doesnot match",400)
        else:
            hash=generate_password_hash(request.form.get("password"))
            result=db.execute("INSERT INTO users (username,hash) VALUES(:username,:hash)",username=request.form.get("username"),hash=hash)
            if not result:
                return apology("username already taken",400)
            rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
            session["user_id"]=rows[0]["id"]


            return redirect("/")
    else:
         return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    count=0
    county=0
    if request.method=="POST":
        if not request.form.get("symbol"):
            return apology("no stock selected",400)
        elif not lookup(request.form.get("symbol")):
            return apology("stock not found",400)
        else:
            result=db.execute("SELECT stock FROM transactions WHERE user_id=:user_id",user_id=session["user_id"])
            z=len(result)
            for x in range(z):
                if(result[x]["stock"]==request.form.get("symbol")):
                    county=x
                    count=1
                    break
            if(count==0):
                return apology("you don't have this stock",400)
            else:
                if not request.form.get("shares"):
                    return apology("no shares selected",400)
                else:
                    a=float(request.form.get("shares"))
                    if a<=0:
                        return apology("wrong number of shares given",400)
                    else:
                        result1=db.execute("SELECT shares FROM transactions WHERE user_id=:user_id",user_id=session["user_id"] )
                        if(result1[county]["shares"]<a):
                            return apology("you choose number of shares which you dont possess",400)
                        else:
                            xo=lookup(request.form.get("symbol")).get("price")
                            mo=xo*a
                            go=db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])
                            mo+=go[0]["cash"]
                            db.execute("UPDATE users SET cash=:cash WHERE id=:id",cash=mo, id=session["user_id"] )
                            db.execute("INSERT INTO history (user_id,transactionx,stock,price,shares,dateandtime) VALUES(:user_id,:transactionx,:stock,:price,:shares,:dateandtime)",user_id=session["user_id"],transactionx="SOLD",stock=request.form.get("symbol"),price=xo,shares=request.form.get("shares"),dateandtime=dt_string)
                            if result1[county]["shares"]==a:
                                db.execute("DELETE FROM transactions WHERE user_id=:user_id AND stock=:stock",user_id=session["user_id"],stock=request.form.get("symbol"))
                            else:
                                db.execute("UPDATE transactions SET shares=:shares WHERE user_id=:user_id AND stock=:stock",shares=result1[county]["shares"]-a,user_id=session["user_id"],stock=request.form.get("symbol"))




                            return redirect("/")
    else:
        resultx=db.execute("SELECT stock FROM transactions WHERE user_id=:user_id",user_id=session["user_id"])
        return render_template("sell.html",result=resultx)

@app.route("/cgpwd", methods=["GET", "POST"])
def cgpwd():
    if request.method=="POST":
        a=request.form.get("password")
        b=request.form.get("username")
        hash=generate_password_hash(request.form.get("password"))

        result=db.execute("UPDATE users SET hash=:hash WHERE username=:username",hash=hash,username=b)
        if not result:
            return apology("username not found",403)
        else:
            return redirect("/login")
    else:
        return render_template("cgpwd.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
