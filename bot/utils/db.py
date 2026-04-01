import sqlite3
import os

DB_NAME = "database.db"

def save_farmer(crop, loc, qty, cost):
    """
    Saves farmer data to the SQLite database.
    """
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS farmer(
            crop TEXT,
            location TEXT,
            qty INT,
            cost INT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute(
            "INSERT INTO farmer (crop, location, qty, cost) VALUES(?,?,?,?)",
            (crop, loc, qty, cost)
        )

        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False
