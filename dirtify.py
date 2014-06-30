#!/usr/bin/env python
import sqlite3
import sys

if __name__ == "__main__":
    dbfile = sys.argv[1]

    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    c.execute("""UPDATE data SET dirty=1""")
    conn.commit()
    conn.close()
