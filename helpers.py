import os
import requests
import urllib.parse
import re
import json
from datetime import datetime, timedelta

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


def isMarketOpen():
    try:
        api_key = os.getenv("API_KEY")
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=SPY&interval=60min&apikey={api_key}'
        response = requests.get(url)
        response.raise_for_status()

        # Parse the JSON response
        data = json.loads(response.text)

        # Check the last updated time of the data
        last_updated = datetime.strptime(
            data['Meta Data']['3. Last Refreshed'], '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()

        # Calculate the time difference between the last updated time and the current time
        time_diff = current_time - last_updated

        # Check if the market is open or closed
        if time_diff.seconds // 3600 >= 2:
            # If the market is closed, calculate the time until the next market open
            market_open_time = datetime.now().replace(
                hour=13, minute=30, second=0, microsecond=0)
            if current_time > market_open_time:
                # If it's past 1:30 PM ET, the market will open the next day
                market_open_time += timedelta(days=1)
            time_until_market_open = market_open_time - current_time

            if time_until_market_open.days > 0:
                return f"US market is closed. It will open in {time_until_market_open.days} days, {time_until_market_open.seconds//3600} hours, and {(time_until_market_open.seconds//60)%60} minutes."
            else:
                return f"US market is closed. It will open in {time_until_market_open.seconds//3600} hours and {(time_until_market_open.seconds//60)%60} minutes."

        else:
            return "US market is open. See your portfolio change in value from time to time."

    except requests.RequestException:
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


def get_symbol(string):
    match = re.search('[A-Za-z]+', string)

    if match:
        return match.group(0)


def get_qty(string):
    match = re.search('\d+', string)

    if match:
        return match.group(0)
