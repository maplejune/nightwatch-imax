#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests, moment, sqlite3
import re, os, logging, logging.handlers

TICKET_FORMAT = re.compile(r"popupSchedule\('(.*)','(.*)','(\d\d:\d\d)','\d*','\d*', '\d*', '(\d*)', '(\d*)',")

LOG_FILE = os.path.join(os.path.dirname(__file__), 'WATCH.log')
DB_FILE = os.path.join(os.path.dirname(__file__), 'TICKET.db')

def getImaxTicketList(theaterCd):
    imaxTicketList = []
    
    for playYMD in [moment.now().add(days=x).strftime('%Y%m%d') for x in range(0, 30)]:
        response = requests.post('http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx', {'theaterCd':theaterCd, 'playYMD':playYMD})
        timeList = BeautifulSoup(response.text).find_all("ul", "timelist")
        
        for time in timeList:
            for ticket in time.find_all('a'):
                if str(ticket).find('IMAX') > -1:
                    rawData = TICKET_FORMAT.findall(str(ticket))
                    
                    if len(rawData) == 1 and len(rawData[0]) == 5:
                        ticketData = rawData[0]
                        
                        movieTitle = ticketData[0]
                        ticketType = ticketData[1]
                        ticketTime = ticketData[2]
                        movieIdx = ticketData[3]
                        ticketDate = ticketData[4]
                        
                        if movieTitle.find('IMAX') > -1 and ticketType.find('IMAX') > -1:
                            imaxTicketList.append({'theaterCd':theaterCd, 'movieIdx':movieIdx, 'movieTitle':movieTitle, 'ticketDate': ticketDate, 'ticketTime': ticketTime})

    return imaxTicketList

if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    currentTime = moment.now().strftime('%Y%m%d%H%M')
    imaxTicketList = getImaxTicketList('0074')
    
    for imaxTicket in imaxTicketList:
        cursor.execute('SELECT * FROM ticket WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND ticketTime=?', (imaxTicket['theaterCd'], imaxTicket['movieIdx'], imaxTicket['ticketDate'], imaxTicket['ticketTime']))
        savedTicket = cursor.fetchone()
        
        if savedTicket is None:
            cursor.execute('INSERT INTO ticket VALUES (?,?,?,?,?)', (imaxTicket['theaterCd'], imaxTicket['movieIdx'], imaxTicket['ticketDate'], imaxTicket['ticketTime'], currentTime))
            print imaxTicket
        else:
            print savedTicket
            
    conn.commit()
    conn.close()
        

        