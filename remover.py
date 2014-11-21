#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3, moment
import re, os, logging, logging.handlers

LOG_FILE = os.path.join(os.path.dirname(__file__), 'WATCH.log')
DB_FILE = os.path.join(os.path.dirname(__file__), 'TICKET.db')

logger = logging.getLogger('NIGHTWATCH-IMAX')
logger.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10240000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def main():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM ticket')
    ticketRawList = cursor.fetchall()
    
    yesterday = moment.now().subtract(days=1)
    currentTimeStr = moment.now().strftime('%Y%m%d%H%M')

    for ticketRaw in ticketRawList:
        if moment.date(ticketRaw[2], '%Y%m%d') < yesterday:
            cursor.execute('INSERT INTO history VALUES (?,?,?,?,?,?)', \
                           (ticketRaw[0], ticketRaw[1], ticketRaw[2], ticketRaw[3], currentTimeStr, ticketRaw[5]))
            cursor.execute('DELETE FROM ticket WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND ticketTime=?', \
                           (ticketRaw[0], ticketRaw[1], ticketRaw[2], ticketRaw[3]))
            
            logger.debug('Old ticket deleted : ' + str((ticketRaw[0], ticketRaw[1], ticketRaw[2], ticketRaw[3])))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()