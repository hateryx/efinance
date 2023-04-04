import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

from dotenv import load_dotenv

load_dotenv()


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.getenv("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"],
            "volume": quote["avgTotalVolume"],
            "marketCap": quote["marketCap"],
        }
    except (KeyError, TypeError, ValueError):
        return None


def company_lookup(symbol):
    """Look up company info for symbol."""

    # Contact API
    try:
        api_key = os.getenv("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/company?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "description": quote["description"],
            "industry": quote["industry"],
            "sector": quote["sector"],
            "website": quote["website"],
            "exchange": quote["exchange"],
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def percent(value):
    """Format value as percentage."""
    return '{:.2%}'.format(value)


def millions(value):
    """Formats a number with commas for thousands, millions, etc."""
    if value is None:
        return "-"

    magnitude = 0
    while abs(value) >= 1000:
        magnitude += 1
        value /= 1000.0

    return f"{value:,.1f} {'KMGTPEZY'[magnitude]}".replace(".0", "")


def top_performing_stocks(explore):

    # Contact API
    try:
        api_key = os.getenv("API_KEY")
        url = f'https://cloud.iexapis.com/stable/stock/market/list/{explore}?token={api_key}'
        response = requests.get(url)

        if response.status_code == 200:
            # retrieve the top 10 performing stocks
            stocks = response.json()[:10]
            return stocks
        else:
            return 'Error retrieving data from IEX Cloud'

        response.raise_for_status()
    except requests.RequestException:
        return 'Error retrieving data from IEX Cloud'


def ordinal(value):
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"
