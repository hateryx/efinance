import sys
import json
import datetime

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, func, cast, Integer

from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, company_lookup, usd, percent, millions, top_performing_stocks, ordinal, get_symbol, get_qty, isMarketOpen

from dotenv import load_dotenv

global MARKET_STATUS
MARKET_STATUS = isMarketOpen()

load_dotenv()

fin_app = Flask(__name__)
fin_app.secret_key = "Hello World"
fin_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
fin_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

fin_app.jinja_env.filters['usd'] = usd
fin_app.jinja_env.filters['percent'] = percent
fin_app.jinja_env.filters['millions'] = millions
fin_app.jinja_env.filters['ordinal'] = ordinal

# test
fin_app.config["SESSION_PERMANENT"] = False
fin_app.config["SESSION_TYPE"] = "filesystem"
Session(fin_app)

db = SQLAlchemy(fin_app)

with fin_app.app_context():
    conn = db.engine.connect()
    db.create_all()


class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    hash = db.Column(db.String(80), nullable=False)
    cash = db.Column(db.Integer, nullable=False, default=10000)

    def __init__(self, id, username, hash, cash):
        self.id = id
        self.username = username
        self.hash = hash
        self.cash = cash


class stock_txn(db.Model):
    txn_id = db.Column(db.Integer, primary_key=True)
    stock = db.Column(db.String(80), nullable=False)
    no_of_shares = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer)
    txn_date = db.Column(db.Date)
    txn_type = db.Column(db.String(80), nullable=False)

    def __init__(self, txn_id, no_of_shares, total_cost, user_id, txn_date, txn_type):
        self.txn_id = txn_id
        self.no_of_shares = no_of_shares
        self.total_cost = total_cost
        self.user_id = user_id
        self.txn_date = txn_date
        self.txn_type = txn_type


class cash_running_bal(db.Model):
    c_bal_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    txn_id = db.Column(db.Integer)
    txn_date = db.Column(db.Date)
    amount_change = db.Column(db.Integer, nullable=False)
    cash_end_bal = db.Column(db.Integer, nullable=False)

    def __init__(self, c_bal_id, user_id, txn_id, txn_date, amount_change, cash_end_bal):
        self.c_bal_id = c_bal_id
        self.user_id = user_id
        self.txn_id = txn_id
        self.txn_date = txn_date
        self.amount_change = amount_change
        self.cash_end_bal = cash_end_bal


class port_ranker(db.Model):
    p_r_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    port_update_date = db.Column(db.Date)
    equity_value = db.Column(db.Integer, nullable=False)
    net_gain_loss = db.Column(db.Integer, nullable=False)
    owned_stocks = db.Column(db.String)
    latest_cash = db.Column(db.Integer)

    def __init__(self, p_r_id, user_id,  port_update_date, equity_value, net_gain_loss, owned_stocks, latest_cash):
        self.p_r_id = p_r_id
        self.user_id = user_id
        self.port_update_date = port_update_date
        self.equity_value = equity_value
        self.net_gain_loss = net_gain_loss
        self.owned_stocks = owned_stocks
        self.latest_cash = latest_cash


def inquire_username(current_user):
    username_query = text("SELECT username FROM users WHERE id = :id")
    username_select = db.session.execute(
        username_query, {'id': current_user}).fetchone()

    username = username_select[0]

    return username


def inquire_latest_cash(current_user):
    cash_query = text(
        "SELECT cash_end_bal FROM cash_running_bal WHERE user_id = :user_id AND c_bal_id = (SELECT MAX(c_bal_id) FROM cash_running_bal WHERE user_id = :user_id)")
    cash_latest_bal = db.session.execute(
        cash_query, {'user_id': current_user}).fetchone()
    current_cash = float(cash_latest_bal[0])

    return current_cash


def inquire_portfolio(current_user):
    query_stock = db.session.query(stock_txn.stock, stock_txn.txn_type, stock_txn.no_of_shares, stock_txn.total_cost)\
        .filter(stock_txn.user_id == current_user)\
        .all()

    stock_hash_map = {}
    cost_hash_map = {}
    buy_hash_map = {}

    for row in query_stock:
        stock, txn_type, no_of_shares, total_cost = row
        if stock not in stock_hash_map:
            stock_hash_map[stock] = 0
            cost_hash_map[stock] = 0
            buy_hash_map[stock] = 0
        if txn_type == "buy":
            stock_hash_map[stock] += no_of_shares
            cost_hash_map[stock] += total_cost
            buy_hash_map[stock] += no_of_shares
        else:
            stock_hash_map[stock] -= no_of_shares

    stock_hash_map_to_list = [{'symbol': key, 'no_of_shares_now_held': value}
                              for key, value in stock_hash_map.items()]

    # shortlist the stocks held
    stock_portfolio = []

    total_share_value = 0

    for each in stock_hash_map_to_list:
        stock_stats = {"stock": "", "no_of_shares": 0,
                       "total_cost": 0, "market_value": 0, "profit_loss": 0}

        if each['no_of_shares_now_held'] > 0:
            total_stock_cost = cost_hash_map[each["symbol"]]
            total_no_of_buy = buy_hash_map[each["symbol"]]
            pro_rata_cost = total_stock_cost * \
                each["no_of_shares_now_held"] / total_no_of_buy

            market_details = lookup(each["symbol"])
            market_price = each["no_of_shares_now_held"] * \
                float(market_details["price"])

            stock_stats["stock"] = each["symbol"]
            stock_stats["no_of_shares"] = each["no_of_shares_now_held"]
            stock_stats["total_cost"] = pro_rata_cost
            stock_stats["market_value"] = market_price
            stock_stats["profit_loss"] = market_price - pro_rata_cost

            total_share_value += market_price

            stock_portfolio.append(stock_stats)

    return stock_portfolio


def update_usersPortValue():

    port_ranker_query = text(
        "SELECT user_id, owned_stocks, latest_cash FROM port_ranker")
    query_result = db.session.execute(port_ranker_query).fetchall()
    port_ranker_update = text(
        "UPDATE port_ranker SET equity_value = :equity_value, net_gain_loss = :net_gain_loss WHERE user_id = :user_id")

    print(query_result)

    for row in query_result:
        current_market_value = 0

        user = row[0]
        stock_holding_info = row[1]
        latest_cash = float(row[2])

        # assuming the stocks held are more than 1
        if stock_holding_info:
            all_stock_subset = stock_holding_info.split(",")

            for elem in all_stock_subset:
                stock_and_qty = elem.split(":")
                stock = get_symbol(stock_and_qty[0])
                qty = int(get_qty(stock_and_qty[1]))

                stock_info = lookup(stock)
                compute_stock_value = stock_info['price'] * qty
                current_market_value += compute_stock_value

            current_equity_value = latest_cash+current_market_value

            db.session.execute(port_ranker_update, {"user_id": user,
                                                    "equity_value": current_equity_value, "net_gain_loss": (current_equity_value-10000)})

            # users_stock_dict_list.append({
            #     "user_id": user,
            #     "market_value": current_market_value,
            #     "total_equity": (latest_cash+current_market_value)
            # })
    db.session.commit()


@fin_app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@fin_app.route('/')
def index():
    try:
        if session["user_id"]:
            return redirect("/portfolio")
        else:
            return render_template("index.html", isMarketOpen=MARKET_STATUS)
    except KeyError:
        return render_template("index.html", isMarketOpen=MARKET_STATUS)


@fin_app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmation")
        if password != confirm_password or not password or not confirm_password:
            return apology("Bad password. Please try to register again.")

        hashed_password = generate_password_hash(password)

        if not username:
            return apology("User input is blank.")

        users_dict = db.session.execute(
            text("SELECT username FROM users")).fetchall()
        username_list = []
        for each in users_dict:
            username_list.append(each[0])

        if username in username_list:
            return apology("Username already exists. Try again another username.")

        current_datetime = datetime.datetime.now()
        txn_date = current_datetime.strftime('%m/%d/%Y %H:%M:%S')

        latest_user_id = db.session.query(
            func.max(users.id)).scalar() or 0
        latest_user_id_toInt = db.session.query(
            cast(latest_user_id, Integer)).scalar()
        current_user_id = latest_user_id_toInt + 1

        try:
            user_insert = text(
                "INSERT INTO users (username, hash, cash) VALUES (:username, :hashed_password, :cash)")

            db.session.execute(
                user_insert, {'username': username, 'hashed_password': hashed_password, 'cash': 10000.00})

            cash_run_bal_insert = text(
                "INSERT INTO cash_running_bal (user_id, txn_id, txn_date, amount_change,cash_end_bal) VALUES (:user_id, :txn_id, :txn_date,:amount_change,:cash_end_bal)")

            db.session.execute(cash_run_bal_insert, {'user_id': current_user_id, 'txn_id': 0,
                                                     'txn_date': txn_date, 'amount_change': 10000, 'cash_end_bal': 10000})

            port_ranker_insert = text(
                "INSERT INTO port_ranker (user_id, port_update_date, equity_value, net_gain_loss, latest_cash) VALUES (:user_id, :port_update_date, 10000, 0, 10000)")

            db.session.execute(port_ranker_insert, {'user_id': current_user_id,
                                                    'port_update_date': txn_date})
        except Exception as e:
            print(e)
            sys.exit()

        db.session.commit()

        return redirect("/login")

    else:
        return render_template("register.html", isMarketOpen=MARKET_STATUS)


@fin_app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        username = request.form.get("username")
        rows = users.query.filter_by(username=username).all()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].hash, request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0].id

        # update_usersPortValue()

        # Redirect user to home page

        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", isMarketOpen=MARKET_STATUS)


@fin_app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@fin_app.route('/refresh')
@login_required
def refresh():
    try:
        update_usersPortValue()
        checkMarketOpen = isMarketOpen()
        global MARKET_STATUS
        MARKET_STATUS = checkMarketOpen
    except Exception:
        return apology("Server is having issues.")

    return redirect("/portfolio")


@fin_app.route('/portfolio')
@login_required
def portfolio():

    current_user = session["user_id"]
    current_cash = inquire_latest_cash(current_user)
    current_datetime = datetime.datetime.now()

    try:
        stock_portfolio = inquire_portfolio(current_user)
        owned_stock_list = []

        total_share_value = 0
        for each in stock_portfolio:
            total_share_value += each["market_value"]
            owned_stock_list.append(
                json.dumps({each["stock"]: each["no_of_shares"]}))

    except Exception:
        return apology("Either the API key is not valid or the API service provider is having issues.")

    username = inquire_username(current_user)
    equity_value = total_share_value + current_cash
    net_gain_loss = equity_value - 10000
    txn_date = current_datetime.strftime('%m/%d/%Y %H:%M:%S')
    owned_stocks = " ,".join(owned_stock_list) or None

    try:
        port_ranker_update = text(
            "UPDATE port_ranker SET port_update_date = :port_update_date, equity_value = :equity_value, net_gain_loss = :net_gain_loss, owned_stocks = :owned_stocks, latest_cash = :latest_cash WHERE user_id = :user_id")
        db.session.execute(port_ranker_update, {
            'user_id': current_user, 'port_update_date': txn_date, 'equity_value': equity_value, 'net_gain_loss': net_gain_loss, 'owned_stocks': owned_stocks, 'latest_cash': current_cash})
    except Exception:
        return apology("Server is having issues.")

    db.session.commit()

    port_ranker_query = text(
        "SELECT username, equity_value, net_gain_loss FROM (SELECT users.username,port_ranker.equity_value,port_ranker.net_gain_loss FROM port_ranker JOIN users ON port_ranker.user_id = users.id) ORDER BY net_gain_loss DESC LIMIT 10")
    leaderboard = db.session.execute(port_ranker_query).fetchall()

    port_userrank_query = text(
        "SELECT COUNT(net_gain_loss) FROM port_ranker WHERE net_gain_loss > (SELECT net_gain_loss from port_ranker WHERE user_id = :user_id)")

    leaders = []
    for row in leaderboard:
        leaders.append(row[0])
    if username in leaders:
        isLeader = True
        rank = leaders.index(username)
    else:
        isLeader = False
        rank = db.session.execute(port_userrank_query, {
                                  'user_id': current_user}).fetchone()
        rank = int(rank[0])

    global MARKET_STATUS
    try:
        MARKET_STATUS = isMarketOpen()
    except Exception:
        pass

    return render_template("portfolio.html", isMarketOpen=MARKET_STATUS, username=username, equity_value=equity_value, net_gain_loss=net_gain_loss, portfolio=stock_portfolio, cash=current_cash, total_share_value=total_share_value, leaderboard=leaderboard, isLeader=isLeader, rank=rank)


@fin_app.route("/explore", methods=['POST'])
@login_required
def explore():
    current_user = session["user_id"]
    current_cash = inquire_latest_cash(current_user)

    explore = request.form.get("explore")
    stock_reco = top_performing_stocks(explore)

    match explore:
        case 'mostactive':
            header = 'Top 10 Stocks With Most Active Volume of the Day'
        case 'gainers':
            header = 'Top 10 Stocks with Highest Gains of the Day'
        case 'losers':
            header = 'Top 10 Stocks with Sharpest Loss of the Day'

    return render_template("quote.html", stock_reco=stock_reco, current_cash=current_cash, header=header, selected=explore)


@fin_app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    current_user = session["user_id"]
    current_cash = inquire_latest_cash(current_user)

    if request.method == "POST":
        symbol = request.form.get("symbol")
        symbol_details = lookup(symbol)

        if not symbol or not symbol_details:
            return apology("Invalid symbol")

        price = symbol_details["price"]
        company = symbol_details["name"]
        volume = symbol_details["volume"]
        marketCap = int(symbol_details["marketCap"])

        company_info = company_lookup(symbol)

        description = company_info["description"]
        industry = company_info["industry"]
        sector = company_info["sector"]
        exchange = company_info["exchange"]
        website = company_info["website"]

        # return render_template("quote.html", symbol=symbol, company=company, price=price, test=company_info, current_cash=current_cash)

        return render_template("quote.html", isMarketOpen=MARKET_STATUS, symbol=symbol, company=company, price=price, description=description, industry=industry, sector=sector, marketCap=marketCap, volume=volume, website=website, exchange=exchange, current_cash=current_cash)

    else:

        # stock_reco = top_performing_stocks(explore="mostactive")

        # return render_template("quote.html", isMarketOpen=MARKET_STATUS, stock_reco=stock_reco, current_cash=current_cash)
        return render_template("quote.html", isMarketOpen=MARKET_STATUS, current_cash=current_cash)


@fin_app.route("/buy", methods=["POST"])
@login_required
def buy():
    """Buy shares of stock"""

    current_user = session["user_id"]
    current_cash = inquire_latest_cash(current_user)

    if request.method == "POST":

        buying_stock = request.form.get("symbol")
        no_of_shares = request.form.get("shares")

        if no_of_shares.isdigit() == False:
            return apology("You did not provide a valid number of shares!")

        no_of_shares = int(no_of_shares)

        stock_details = lookup(buying_stock)

        if not buying_stock or not stock_details:
            return apology("You did not provide a valid symbol!")

        if no_of_shares <= 0 or no_of_shares % 1 != 0 or not no_of_shares:
            return apology("The specified number of shares you inputted is invalid.")

        cost_of_shares = stock_details["price"] * no_of_shares

        current_datetime = datetime.datetime.now()
        txn_date = current_datetime.strftime('%m/%d/%Y %H:%M:%S')

        ending_cash_on_hand = current_cash - cost_of_shares

        if ending_cash_on_hand < 0:
            return apology("Sorry but your funds are insufficient to buy the stocks")

        max_stock_txn_id = db.session.query(
            func.max(stock_txn.txn_id)).scalar() or 0
        max_stock_txn_id_toInt = db.session.query(
            cast(max_stock_txn_id, Integer)).scalar()
        current_stock_txn_id = max_stock_txn_id_toInt + 1

        try:
            # stock_txn update
            stock_txn_insert = text(
                "INSERT INTO stock_txn (stock, no_of_shares, total_cost, user_id, txn_date, txn_type) VALUES (:buying_stock, :no_of_shares, :cost_of_shares, :current_user, :txn_date, :txn_type)")
            db.session.execute(
                stock_txn_insert, {'buying_stock': buying_stock, 'no_of_shares': no_of_shares, 'cost_of_shares': cost_of_shares, 'current_user': current_user, 'txn_date': txn_date, 'txn_type': "buy"})

            # cash_run_bal update
            cash_run_bal_insert = text(
                "INSERT INTO cash_running_bal (user_id, txn_id, txn_date, amount_change,cash_end_bal) VALUES (:user_id, :txn_id, :txn_date,:amount_change,:cash_end_bal)")
            db.session.execute(cash_run_bal_insert, {'user_id': current_user, 'txn_id': current_stock_txn_id,
                                                     'txn_date': txn_date, 'amount_change': cost_of_shares*-1, 'cash_end_bal': ending_cash_on_hand})

        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

        db.session.commit()

        return redirect("/")


@fin_app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    current_user = session["user_id"]
    transactions = db.session.execute(text(
        "SELECT * FROM stock_txn WHERE user_id = :current_user"), {'current_user': current_user})

    cash_history = db.session.execute(text(
        "SELECT * FROM cash_running_bal WHERE user_id = :current_user"), {'current_user': current_user})

    cash_history = db.session.execute(text(
        "SELECT * FROM (SELECT * FROM cash_running_bal JOIN stock_txn ON cash_running_bal.txn_id = stock_txn.txn_id) WHERE user_id = :current_user"), {'current_user': current_user})

    return render_template("history.html", isMarketOpen=MARKET_STATUS, transactions=transactions, cash_history=cash_history)


@fin_app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    current_user = session["user_id"]

    current_cash = inquire_latest_cash(current_user)

    stock_holdings = inquire_portfolio(current_user)

    stock_owned = []
    for i in range(0, len(stock_holdings)):
        stock_owned.append(stock_holdings[i]["stock"])

    stock_hash_map = {}
    for each in stock_holdings:
        key = each['stock']
        stock_hash_map[key] = 0
        stock_hash_map[key] += each['no_of_shares']

    if request.method == "POST":
        sell_symbol = request.form.get("symbol")
        shares_to_sell = request.form.get("shares")

        if not sell_symbol or sell_symbol not in stock_owned:
            return apology("You cannot sell a stock that you do not own!")

        if int(shares_to_sell) <= 0 or int(shares_to_sell) % 1 != 0 or not shares_to_sell:
            return apology("The input value is not valid for selling shares!")

        shares_owned = stock_hash_map[sell_symbol]

        if int(shares_to_sell) > shares_owned:
            return apology("You do not have enough shares to sell!")

        current_datetime = datetime.datetime.now()
        txn_date = current_datetime.strftime('%m/%d/%Y %H:%M:%S')

        try:
            stock_details = lookup(sell_symbol)
        except TypeError:
            return apology("Apologies, there's a problem in fetching the stock price right now. Please try again later.")

        sale_proceeds = round(stock_details["price"], 2) * int(shares_to_sell)
        sale_proceeds = round(sale_proceeds, 2)

        updated_cash = current_cash + sale_proceeds

        try:
            max_stock_txn_id = db.session.query(
                func.max(stock_txn.txn_id)).scalar() or 0
            max_stock_txn_id_toInt = db.session.query(
                cast(max_stock_txn_id, Integer)).scalar()
            current_stock_txn_id = max_stock_txn_id_toInt + 1

            # stock_txn update
            stock_txn_insert_sell = text(
                "INSERT INTO stock_txn (stock, no_of_shares, total_cost, user_id, txn_date, txn_type) VALUES (:stock, :no_of_shares, :total_cost, :user_id, :txn_date, :txn_type)")

            db.session.execute(stock_txn_insert_sell, {
                               'stock': sell_symbol, 'no_of_shares': shares_to_sell, 'total_cost': sale_proceeds, 'txn_date': txn_date, 'user_id': current_user, 'txn_type': 'sell'})

            # cash_run_bal update
            cash_run_bal_insert = text(
                "INSERT INTO cash_running_bal (user_id, txn_id, txn_date, amount_change,cash_end_bal) VALUES (:user_id, :txn_id, :txn_date,:amount_change,:cash_end_bal)")
            db.session.execute(cash_run_bal_insert, {'user_id': current_user, 'txn_id': current_stock_txn_id,
                               'txn_date': txn_date, 'amount_change': sale_proceeds, 'cash_end_bal': updated_cash})

        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

        db.session.commit()

        return redirect("/portfolio")
    else:

        return render_template("sell.html", isMarketOpen=MARKET_STATUS, portfolio=stock_holdings, stock_owned=stock_owned)


conn.close()

if __name__ == '__main__':
    fin_app.run(debug=True)
