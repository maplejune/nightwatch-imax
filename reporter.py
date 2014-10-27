#!/usr/bin/python
# -*- coding: utf-8 -*-

from twython import Twython
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

def getMovieInfo(cursor, movieIdx):
    cursor.execute('SELECT * FROM movie WHERE movieIdx=?', (movieIdx,))
    movieInfo = cursor.fetchone()
    
    movieTitle = ''
    movieReleaseDate = ''
    
    if movieInfo is None:
        response = requests.get('http://m.cgv.co.kr/WebApp/Movie/movieDetail.aspx?MovieIdx=%d'%movieIdx)

        movieTitleRaw = re.search(u'<article class="title">(.+)</article>', response.text)
        if movieTitleRaw:
            movieTitle = movieTitleRaw.groups()[0]

        movieReleaseDateRaw = re.search(u'<article class="txt1">.*(\d{4}-\d{2}-\d{2}) 개봉</article>', response.text)
        if movieReleaseDateRaw:
            movieReleaseDate = movieReleaseDateRaw.groups()[0]
            
        if movieTitle != '' and movieReleaseDate != '':
            cursor.execute('INSERT INTO movie VALUES (?,?,?)', (movieIdx, movieTitle, movieReleaseDate))
    else:
        movieTitle = movieInfo[1]
        movieReleaseDate = movieInfo[2]
    
    return {'movieTitle': movieTitle, 'movieReleaseDate': movieReleaseDate}

def sendTweet(apiInfo, messageData):
    twitter = Twython(apiInfo[0], apiInfo[1], apiInfo[2], apiInfo[3])
    message = u'%s %s월 %s일 예매가 열렸습니다. %s 예매가능! #%s' % (messageData[0], 
                                                                   int(messageData[1][4:6]), 
                                                                   int(messageData[1][6:8]), 
                                                                   ' '.join([p for p in messageData[2]]),
                                                                   apiInfo[4])
    print message
    #twitter.update_status(status=message)    

if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for theaterCd in ['0074']:
        cursor.execute('SELECT * FROM theater WHERE theaterCd=?', (theaterCd,))
        apiInfo = cursor.fetchone()
    
        if apiInfo is not None:    
            cursor.execute('SELECT DISTINCT movieIdx FROM ticket WHERE theaterCd=? AND isReported=0', (theaterCd,))
            movieIdxRawList = cursor.fetchall()

            for movieIdxRaw in movieIdxRawList:
                movieIdx = movieIdxRaw[0]

                movieInfo = getMovieInfo(cursor, movieIdx)
                movieTitle = movieInfo['movieTitle']
                movieReleaseDate = moment.date(movieInfo['movieReleaseDate'])

                cursor.execute('SELECT DISTINCT ticketDate FROM ticket WHERE theaterCd=? AND movieIdx=? AND isReported=0', (theaterCd, movieIdx,))
                ticketDateRawList = cursor.fetchall()

                for ticketDateRaw in ticketDateRawList:
                    ticketDate = ticketDateRaw[0]

                    if moment.date(ticketDate, 'YYYYMD') >= movieReleaseDate:           
                        cursor.execute('SELECT DISTINCT ticketTime FROM ticket WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND isReported=0', \
                                       (theaterCd, movieIdx,ticketDate,))
                        ticketTimeRawList = cursor.fetchall()
                        ticketTimeList = sorted([ticketTimeRaw[0] for ticketTimeRaw in ticketTimeRawList])

                        sendTweet(apiInfo, (movieTitle, ticketDate, ticketTimeList))

    conn.commit()
    conn.close()
    