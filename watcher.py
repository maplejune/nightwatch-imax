#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests, moment, sqlite3
import re, os, time, logging, logging.handlers
import reporter, remover

TICKET_FORMAT = re.compile(r"popupSchedule\('(.*)','(.*)','(\d\d:\d\d)','\d*','\d*', '(\d*)', '\d*', '(\d*)',")
USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19'
HEADERS = {'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4',
            'Upgrade-Insecure-Requests': 1,
            'Referer': 'http://m.cgv.co.kr/Schedule/',
            'User-Agent': USER_AGENT}

LOG_FILE = os.path.join(os.path.dirname(__file__), 'WATCH.log')
DB_FILE = os.path.join(os.path.dirname(__file__), 'TICKET.db')
DUMMY_ID = "-1"

logger = logging.getLogger('NIGHTWATCH-IMAX')
logger.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10240000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def getCookies():
    response = requests.get('http://m.cgv.co.kr/Schedule/', headers=HEADERS)

    return dict(response.cookies)

def getImaxTicketList(theaterCd, needTuple=False):
    cookies = getCookies()
    imaxTicketList = []

    for playYMD in [moment.now().add(days=x).strftime('%Y%m%d') for x in range(0, 30)]:
        response = requests.post('http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx', data={'theaterCd':theaterCd, 'playYMD':playYMD, 'src':''}, timeout=5, headers=HEADERS, cookies=cookies)
        timeList = BeautifulSoup(response.text).find_all("div", "time borderTopNone")

        time.sleep(1)

        for playTime in timeList:
            movieType = str(playTime.find('span', 'lo_h'))
            
            if movieType.find('IMAX') > -1:
                for ticket in playTime.find_all('a'):
                    rawData = TICKET_FORMAT.findall(str(ticket))
    
                    if len(rawData) == 1 and len(rawData[0]) == 5:
                        ticketData = rawData[0]
    
                        movieTitle = ticketData[0]
                        ticketType = ticketData[1]
                        ticketTime = ticketData[2]
                        movieIdx = ticketData[3]
                        ticketDate = ticketData[4]
    
                        if needTuple:
                            imaxTicketList.append((theaterCd, int(movieIdx), unicode(ticketDate), unicode(ticketTime)))
                        else:
                            imaxTicketList.append({'theaterCd':theaterCd, 'movieIdx':movieIdx, 'movieTitle':movieTitle, 'ticketDate': ticketDate, 'ticketTime': ticketTime})

    return imaxTicketList

def isValidTicket(ticket):
    return ticket['theaterCd'] and ticket['movieIdx'] and ticket['ticketDate'] and ticket['ticketTime']

if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for theaterCd in ['0074', '0013', '0014', '0054', '0199', '0181']:
        currentTime = moment.now().strftime('%Y%m%d%H%M')
        imaxTicketList = getImaxTicketList(theaterCd)

        for imaxTicket in imaxTicketList:
            query = (imaxTicket['theaterCd'], imaxTicket['movieIdx'], imaxTicket['ticketDate'], imaxTicket['ticketTime'])

            if not isValidTicket(imaxTicket):
                logger.debug('Wrong ticket : ' + str(query))
                continue

            cursor.execute('SELECT * FROM ticket WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND ticketTime=?', query)
            savedTicket = cursor.fetchone()

            if savedTicket is None:
                cursor.execute('INSERT INTO ticket VALUES (?,?,?,?,?,?)', (imaxTicket['theaterCd'], \
                                                                           imaxTicket['movieIdx'], \
                                                                           imaxTicket['ticketDate'], \
                                                                           imaxTicket['ticketTime'], \
                                                                           currentTime, \
                                                                           DUMMY_ID))
                logger.debug('New ticket : ' + str(query))
            else:
                logger.debug('Already detected : ' + str(query))

    conn.commit()
    conn.close()

    try:
        reporter.main()
        remover.main()
    except Exception as error:
        logger.error(error)

