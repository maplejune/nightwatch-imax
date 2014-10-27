#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests, moment, sqlite3
import re, os, logging, logging.handlers

LOG_FILE = os.path.join(os.path.dirname(__file__), 'WATCH.log')
DB_FILE = os.path.join(os.path.dirname(__file__), 'TICKET.db')

logger = logging.getLogger('NIGHTWATCH-IMAX')
logger.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10240000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT movieIdx FROM ticket WHERE theaterCd=? AND isReported=0', ('0074',))
    movieIdxRawList = cursor.fetchall()

    for movieIdxRaw in movieIdxRawList:
        movieIdx = movieIdxRaw[0]
        
        cursor.execute('SELECT DISTINCT ticketDate FROM ticket WHERE theaterCd=? AND movieIdx=? AND isReported=0', ('0074', movieIdx,))
        ticketDateRawList = cursor.fetchall()
        
        for ticketDateRaw in ticketDateRawList:
            ticketDate = ticketDateRaw[0]
            
            cursor.execute('SELECT DISTINCT ticketTime FROM ticket WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND isReported=0', ('0074', movieIdx,ticketDate,))
            ticketTimeRawList = cursor.fetchall()
            
            ticketTimeList = sorted([ticketTimeRaw[0] for ticketTimeRaw in ticketTimeRawList])

            print movieIdx, ticketDate, ticketTimeList
    
    conn.close()
    