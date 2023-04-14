from app import fin_app, db
import sqlite3

with fin_app.app_context():
    db.create_all()

    conn = sqlite3.connect('sqlite:///finance.db')
    cursor = conn.cursor()

    # cursor.execute('''ALTER TABLE port_ranker ADD COLUMN owned_stocks TEXT''')
    cursor.execute(
        '''ALTER TABLE port_ranker ADD COLUMN latest_cash NUMERIC, latest_stock_value NUMERIC''')

    cur = conn.cursor()

    conn.commit()
    conn.close()
