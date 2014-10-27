#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sqlite3, json

DB_FILE = os.path.join(os.path.dirname(__file__), 'TICKET.db')
API_FILE = os.path.join(os.path.dirname(__file__), 'API.txt')

if __name__ == "__main__":
    try:
        os.remove(DB_FILE)
    except OSError:
        pass
    
    conn = sqlite3.connect(DB_FILE)

    conn.execute('''CREATE TABLE theater
       (appKey        TEXT     NOT NULL,
       appSecret      TEXT    NOT NULL,
       oauthKey       TEXT    NOT NULL,
       oauthSecret    TEXT    NOT NULL,
       theaterName    TEXT    NOT NULL,
       theaterCd      TEXT    NOT NULL);''')

    conn.execute('''CREATE INDEX theaterInfoIndex
        on theater (theaterCd);''')
    
    apiInfoList = json.load(open(API_FILE))
    
    for apiInfo in apiInfoList:
        conn.execute('INSERT INTO theater VALUES (?,?,?,?,?,?)', (apiInfo['apiKey'], \
                                                                    apiInfo['apiSecret'],  \
                                                                    apiInfo['oauthKey'],  \
                                                                    apiInfo['oauthSecret'], \
                                                                    apiInfo['theaterName'], \
                                                                    apiInfo['theaterCd']))
    
    conn.execute('''CREATE TABLE movie
       (movieIdx        INTEGER     NOT NULL,
       movieTitle       TEXT    NOT NULL,
       releaseDate      TEXT    NOT NULL);''')

    conn.execute('''CREATE INDEX movieInfoIndex
        on movie (movieIdx);''')

    conn.execute('''CREATE TABLE ticket
       (theaterCd       TEXT    NOT NULL,
       movieIdx        INTEGER     NOT NULL,
       ticketDate      TEXT    NOT NULL,
       ticketTime      TEXT    NOT NULL,
       insertTime      TEXT    NOT NULL,
       isReported       INTEGER    NOT NULL);''')

    conn.execute('''CREATE INDEX movieIndex
        on ticket (theaterCd, movieIdx);''')
    
    conn.execute('''CREATE INDEX ticketIndex
        on ticket (theaterCd, movieIdx, ticketDate);''')
    
    conn.execute('''CREATE INDEX ticketAllIndex
        on ticket (theaterCd, movieIdx, ticketDate, ticketTime);''')
    
    conn.commit()
    conn.close()