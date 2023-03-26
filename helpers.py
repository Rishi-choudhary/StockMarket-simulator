from flask import redirect, render_template, session
from functools import wraps
import nsepy as nse



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
    try:
        data = nse.live.get_quote(symbol=sym)['data'][0]
      
    
        return {
            "name":data['companyName'],
            "symbol":data["symbol"],
            "price": float(data["lastPrice"]) 
            
        }

    except  (KeyError, TypeError, ValueError):
        return None  
    

def inr(value):
    """Format value as inr."""
    return f"₹{(value):,.2f}"