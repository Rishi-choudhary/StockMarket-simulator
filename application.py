from flask import Flask, flash, jsonify, redirect, render_template, request, session ,url_for
from flask_session import Session
from helpers import apology, login_required , lookup ,inr
import json
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3




app = Flask(__name__)


app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

database = sqlite3.connect('finance.db' ,check_same_thread=False)
db = database.cursor()


@app.route("/")
def index():
    
    if request.method == "GET":
        session.clear()
        return render_template("index.html")

    
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    id = session['user_id']
    username = db.execute("SELECT username FROM user WHERE id= ?",(id,)).fetchall()
    symbol = request.form.get("symbol")

    # if GET method, return quote.html form
    if request.method == "POST":
        return redirect(url_for('quote_details', sym=symbol))

    # if POST method, get info from form, make sure it's a valid stock
    else:
        return render_template("quote.html",username=username[0][0])
        
@app.route("/quote/<sym>")
@login_required
def quote_details(sym):
    id = session['user_id']
    username = db.execute("SELECT username FROM user WHERE id= ?",(id,)).fetchall()
    try:
    # lookup ticker symbol from quote.html form
        symbol = lookup(sym)
        return render_template("quoted.html", symbol=symbol,username=username[0][0])
        
    # if lookup() returns None, it's not a valid stock symbol
    except(IndexError):         
        # Return template with stock quote, passing in symbol dict
        return apology("Must be a valid Symbol")

@app.route("/login", methods=["GET", "POST"])
def login():
    
    session.clear()
  # if form is submited
      # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM user WHERE username =?",(request.form.get("username"),)).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/home")

    else:
        return render_template("login.html")

    
@app.route("/home")
@login_required
def home():    
    if request.method == "GET":
        
        id = session['user_id']

        username = db.execute("SELECT username FROM user WHERE id= ?",(id,)).fetchall()
                               
        return render_template("home.html",username=username[0][0])



def buy(symbol,shares):    
    
    try:
        # lookup ticker symbol from quote.html form
        quote = lookup(symbol)
        # if lookup() returns None, it's not a valid stock symbol
    except(IndexError):         
            # Return template with stock quote, passing in symbol dict
        return apology("Must be a valid Symbol")



    # return apology if shares not provided. buy form only accepts positive integers
    if not shares:
        return apology("must provide number of shares", 403)
    
    symbol = symbol.upper()
    shares = int(shares)
    purchase = quote['price'] * shares

    # make sure user can afford current stock, checking amount of cash in user table

    # select this user's cash balance from user table
    id=session["user_id"]
    balance = db.execute("SELECT cash FROM user WHERE id = ?",(id,)).fetchall()
    balance = balance[0][0]
    remainder = balance - purchase

    # if purchase price exceeds balance, return error
    if remainder < 0:
        return apology("insufficient funds", 403)

    # query portfolio table for row with this userid and stock symbol:
    row = db.execute("SELECT * FROM portfolio WHERE userid = ? AND symbol = ?",(id,symbol,)).fetchall()

    # if row doesn't exist yet, create it but don't update shares
    if len(row) != 1:
        db.execute("INSERT INTO portfolio (userid, symbol,share,original_price) VALUES (?, ?,?,?)",(id,symbol,0,quote['price'],))
        
    oldshares = 0
    oldsharedata =  db.execute("SELECT share FROM portfolio WHERE userid = ? AND symbol = ?",(id,symbol,)).fetchall()
    # get previous number of shares owned
    if len(oldsharedata) != 0:
        oldshares = oldsharedata[0][0]

        
    # add purchased shares to previous share number
    newshares = oldshares + shares

    # update shares in portfolio table
    db.execute("UPDATE portfolio SET share = ? WHERE userid = ? AND symbol = ?",(newshares,id,symbol,))

    # update cash balance in user table
    db.execute("UPDATE user SET cash = ? WHERE id = ?",(remainder,id,))
    
    database.commit()

    # update history table
    # db.execute("INSERT INTO history (userid, symbol, shares, method, price) VALUES (:userid, :symbol, :shares, 'Buy', :price)",
    #             userid=session["user_id"], symbol=symbol, shares=shares, price=quote['price'])

    # redirect to index page
    return redirect("/wallet")

def sell(symbol,shares):

    id=session["user_id"]
    
    try:
        # lookup ticker symbol from quote.html form
        quote = lookup(symbol)
        # if lookup() returns None, it's not a valid stock symbol
    except(IndexError):         
            # Return template with stock quote, passing in symbol dict
        return apology("Must be a valid Symbol")
    
    
    
    rows = db.execute("SELECT * FROM portfolio WHERE userid = ? AND symbol = ?",(id,symbol,)).fetchall()

    # return apology if symbol invalid/ not owned
    if len(rows) != 1:
        return apology("must provide valid stock symbol", 403)

    # return apology if shares not provided. buy form only accepts positive integers
    if not shares:
        return apology("must provide number of shares", 403)

     # current shares of this stock
    oldshares = rows[0][2]

    # cast shares from form to int
    shares = int(shares)

    # return apology if trying to sell more shares than own
    if shares > oldshares:
        return apology("shares sold can't exceed shares owned", 403)

    # get current value of stock price times shares
    sold = quote['price'] * shares

    # add value of sold stocks to previous cash balance
    cash = db.execute("SELECT cash FROM user WHERE id = ?", (id,)).fetchall()
    cash = cash[0][0]
    cash = cash + sold



    # update cash balance in user table
    db.execute("UPDATE user SET cash = ? WHERE id = ?",(cash,id,))

    # subtract sold shares from previous shares
    newshares = oldshares - shares



    # if shares remain, update portfolio table with new shares
    if shares > 0:
        db.execute("UPDATE portfolio SET share = ? WHERE userid = ? AND symbol = ?",(newshares,id,symbol,))

    # otherwise delete stock row because no shares remain
    else:
        db.execute("DELETE FROM portfolio WHERE symbol = ?AND userid = ?",(symbol,id,))

   
    database.commit()
    # redirect to index page
    return redirect("/wallet")

    
 
@app.route("/trade",methods=["GET","POST"])
@login_required
def trade():
    if request.method == "GET":
        id = session['user_id']
        username = db.execute("SELECT username FROM user WHERE id= ?",(id,)).fetchall()
        return render_template("trade.html",username=username[0][0])
    else:
        symbol = request.form.get("symbol")
        share = request.form.get("shares")
        
        if request.form.get("buy") == "buy":
            return buy(symbol,share)
        elif request.form.get("sell") == "sell":
            return sell(symbol,share)
        elif request.form.get("details") == "details":
            return redirect(url_for("quote_details",sym=symbol))



@app.route("/wallet")
@login_required
def wallet():
    id = session['user_id']
    username = db.execute("SELECT username FROM user WHERE id= ?",(id,)).fetchall()
    """Show portfolio of stocks"""
    id=session["user_id"]
    # select user's stock portfolio and cash total
    rows = db.execute("SELECT * FROM portfolio WHERE userid = ?", (id,)).fetchall()
    cash = db.execute("SELECT cash FROM user WHERE id = ?", (id,)).fetchall()
    # get cash value float
    cash = cash[0][0]
    # this will be total value of all stock holdings and cash
    sum = cash

    data = list()
    
    for row in rows:
        if row[2] != 0:
            look = lookup(row[1])
            tempdict = dict()
            tempdict['name'] = look["name"]
            tempdict['shares'] = row[2]
            tempdict['price'] = look['price']
            tempdict["total"] = tempdict['price'] * row[2]
            tempdict['symbol'] = look['symbol']
            if look['price'] > row[3]:
                tempdict['profit'] = True
                tempdict['profit_amount'] = round((tempdict['price'] - row[3]),3)
            else:
                tempdict['profit'] = False
                tempdict['loss_amount'] = round((row[3] - tempdict['price']),2)
            
            
            sum += tempdict['total'] 
            
            tempdict['price'] = inr(tempdict['price'])
            tempdict['total'] = inr(tempdict['total'])
            data.append(tempdict)
        
    
    return render_template("wallet.html", rows=data, cash=inr(cash), sum=inr(sum),username=username[0][0])



@app.route("/reset")
def reset():
    if request.method == "GET":
        id = session['user_id']
        db.execute("DELETE FROM portfolio WHERE userid = ?",(id,))
        db.execute("UPDATE user SET cash = ? WHERE id = ?",(10000,id,))
        database.commit()
        return redirect("/wallet")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register",methods=["GET","POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (submitting the register form)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)
        
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        
        
        
        rows = db.execute("SELECT * FROM user WHERE username =?", (username,)).fetchall()
        if len(rows) != 0:
            return apology("username is already taken", 403)
        
    
        
        db.execute("INSERT INTO user (username, hash,cash) VALUES (?,?,?)" ,(username,password,10000) )
        database.commit()

        # redirect to login page
        return redirect("/home")
        
    else:
        return render_template("register.html")

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "GET":
        return render_template("password.html")
    else:
        
        oldpass = request.form.get("oldpass")
        newpass = request.form.get("newpass")
        confirm = request.form.get("confirm")
        
        
        if not oldpass or not newpass or not confirm:
            return apology("missing old or new password",403)
        
        id = session["user_id"]
        hash = db.execute("SELECT hash FROM user WHERE id = ?", (id,)).fetchall()
        hashpasswrod = hash[0][0]
        
        if not check_password_hash(hashpasswrod, oldpass):
            return apology("old password incorrect", 403)
        
        db.execute("UPDATE user SET hash = ? WHERE id = ?",(hashpasswrod,id,))
        database.commit()
        
        if newpass != confirm:
            return apology("new password do not match", 403)
        
        return redirect("/logout")

       
       
