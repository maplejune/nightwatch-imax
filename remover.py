#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3, moment
import re, os, logging, logging.handlers
import watcher

LOG_FILE = os.path.join(os.path.dirname(__file__), 'DELETE.log')
DB_FILE = os.path.join(os.path.dirname(__file__), 'TICKET.db')

logger = logging.getLogger('NIGHTWATCH-IMAX-REMOVER')
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
            
            logger.debug('Old ticket deleted : ' + str(ticketRaw))
    
    cursor.execute('SELECT DISTINCT theaterCd FROM ticket')
    theaterCdRawList = cursor.fetchall()

    for theaterCdxRaw in theaterCdRawList:
        if len(theaterCdxRaw) == 1:
            theaterCd = theaterCdxRaw[0]

            cursor.execute('SELECT theaterCd, movieIdx, ticketDate, ticketTime FROM ticket WHERE theaterCd=? AND statusId!=-1', (theaterCd,))
            ticketLocalList = cursor.fetchall()

            if type(ticketLocalList) is list and len(ticketLocalList) > 0:
                ticketRemoteList = watcher.getImaxTicketList(theaterCd, True)
                
                ticketLocalSet = frozenset(ticketLocalList)
                ticketRemoteSet = frozenset(ticketRemoteList)
                
                fakeTicketSet = ticketLocalSet.difference(ticketRemoteSet)
                
                for fakeTicket in fakeTicketSet:
                    cursor.execute('SELECT * FROM ticket WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND ticketTime=?', (fakeTicket[0], fakeTicket[1], fakeTicket[2], fakeTicket[3]))
                    ticketRaw = cursor.fetchone()
                    
                    currentTime = moment.now()
                    ticketInsertTime = moment.date(ticketRaw[4], 'YYYYMMDDHHmm')
                    
                    timeDiff = currentTime - ticketInsertTime
                    
                    if timeDiff.seconds < 3600:
                        cursor.execute('INSERT INTO history VALUES (?,?,?,?,?,?)', (ticketRaw[0], ticketRaw[1], ticketRaw[2], ticketRaw[3], currentTimeStr, ticketRaw[5]))
                        cursor.execute('DELETE FROM ticket WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND ticketTime=?', (ticketRaw[0], ticketRaw[1], ticketRaw[2], ticketRaw[3]))
                
                        logger.debug('Possible fake ticket : ' + str(ticketRaw))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()