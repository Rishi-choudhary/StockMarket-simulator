from flask import redirect, render_template, session
from functools import wraps
from bsedata.bse import BSE
bsedata = BSE()
import json


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
    
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function





    
def lookup(sym):    
    
    f = open('fasf.json')
    data = json.load(f)
    code = 0
    for i in data['data']:
        if sym == i["company"]:
            code = i['code']
    
    try:
        q = bsedata.getQuote(str(code))
        
        return {
            "name":q['companyName'],
            "symbol":q['securityID'],
            "price":float(q['currentValue'])
        }    
    except  (KeyError, TypeError, ValueError):
        return None 
    # try:
    #     data = nse.live.get_quote(symbol=sym)['data'][0]
      
    
    #     return {
    #         "name":data['companyName'],
    #         "symbol":data["symbol"],
    #         "price": float(data["lastPrice"]) 
            
    #     }

    # except  (KeyError, TypeError, ValueError):
    #     return None  
    

def inr(value):
    """Format value as inr."""
    return f"₹{(value):,.2f}"
