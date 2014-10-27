#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sqlite3

DB_FILE = os.path.join(os.path.dirname(__file__), 'TICKET.db')

if __name__ == "__main__":
    try:
        os.remove(DB_FILE)
    except OSError:
        pass
    
    conn = sqlite3.connect(DB_FILE)
    
    conn.execute('''CREATE TABLE ticket
       (theaterCd       TEXT    NOT NULL,
       movieIdx        INTEGER     NOT NULL,
       ticketDate      TEXT    NOT NULL,
       ticketTime      TEXT    NOT NULL,
       insertTime      TEXT    NOT NULL,
       isReported       INTEGER    NOT NULL);''')

    conn.execute('''CREATE INDEX ticketIndex
        on ticket (theaterCd, movieIdx, ticketDate);''')
    
    conn.execute('''CREATE INDEX ticketAllIndex
        on ticket (theaterCd, movieIdx, ticketDate, ticketTime);''')
    
    conn.close()