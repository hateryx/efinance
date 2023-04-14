from app import fin_app, db
import sqlite3

with fin_app.app_context():
    db.create_all()

    conn = sqlite3.connect('sqlite:///finance.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 10000.00)''')
    cursor.execute('''CREATE TABLE stock_txn (txn_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, stock TEXT NOT NULL, no_of_shares NUMERIC NOT NULL, total_cost NUMERIC NOT NULL, user_id NUMERIC NOT NULL, txn_date DATE NOT NULL, txn_type TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE cash_running_bal
      (c_bal_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER, txn_id INTEGER, txn_date DATE NOT NULL, amount_change NUMERIC NOT NULL, cash_end_bal NUMERIC NOT NULL)''')

    cursor.execute('''CREATE TABLE port_ranker
      (p_r_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER, port_update_date DATE NOT NULL, equity_value NUMERIC NOT NULL, net_gain_loss NUMERIC NOT NULL, owned_stocks TEXT, latest_cash NUMERIC)''')

    cur = conn.cursor()

# # Get the list of tables in the database
#     table_names = cur.execute(
#         "SELECT name FROM sqlite_master WHERE type='table';").fetchall()

# # Iterate over the tables and print the columns
#     for table in table_names:
#         table_name = table[0]
#         columns = cur.execute(f"PRAGMA table_info({table_name});").fetchall()
#         print(f"Columns of table {table_name}:")
#         for column in columns:
#             print(column[1])

    conn.commit()
    conn.close()
