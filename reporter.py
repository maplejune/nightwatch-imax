#!/usr/bin/python
# -*- coding: utf-8 -*-

from twython import Twython, TwythonError
import requests, moment, sqlite3
import re, os, logging, logging.handlers

DB_FILE = os.path.join(os.path.dirname(__file__), 'TICKET.db')
DUMMY_ID = "-1"

def getMovieInfo(cursor, movieIdx):
    cursor.execute('SELECT * FROM movie WHERE movieIdx=?', (movieIdx,))
    movieInfo = cursor.fetchone()
    
    movieTitle = ''
    movieReleaseDate = ''
    
    if movieInfo is None:
        response = requests.get('http://m.cgv.co.kr/WebApp/MovieV4/movieDetail.aspx?MovieIdx=%d'%movieIdx)

        movieTitleRaw = re.search(u'<strong class="tit">(.+)</strong>', response.text)
        if movieTitleRaw:
            movieTitle = movieTitleRaw.groups()[0]

        movieReleaseDateRaw = re.search(u'<span class="mi_openday">.*(\d{4}\.\d{2}\.\d{2}) 개봉', response.text)
        if movieReleaseDateRaw:
            movieReleaseDate = movieReleaseDateRaw.groups()[0]
            
        if movieTitle != '' and movieReleaseDate != '':
            movieReleaseDate = moment.date(movieReleaseDate, '%Y.%m.%d')
            cursor.execute('INSERT INTO movie VALUES (?,?,?)', (movieIdx, movieTitle, movieReleaseDate.strftime('%Y-%m-%d')))
    else:
        movieTitle = movieInfo[1]
        movieReleaseDate =  moment.date(movieInfo[2])
    
    return {'movieTitle': movieTitle, 'movieReleaseDate': movieReleaseDate}

def sendTweet(apiInfo, messageData):
    twitter = Twython(apiInfo[0], apiInfo[1], apiInfo[2], apiInfo[3])
    message = u'%s %s월 %s일 예매가 열렸습니다. %s 예매가능! #%s' % \
                (messageData[0], int(messageData[1][4:6]), int(messageData[1][6:8]), ' '.join([p for p in messageData[2]]), apiInfo[4])
    
    try:
        statusInfo = twitter.update_status(status=message)
        return statusInfo['id']
    except TwythonError as twitError:
        if twitError.msg.find('duplicate') > 0:
            message = u'%s %s월 %s일 예매가 다시 열렸습니다. %s 예매가능! #%s' % \
                (messageData[0], int(messageData[1][4:6]), int(messageData[1][6:8]), ' '.join([p for p in messageData[2]]), apiInfo[4])
                
            statusInfo = twitter.update_status(status=message)
            return statusInfo['id']
        else:    
            return False

def main():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for theaterCd in ['0074', '0013', '0014', '0054']:
        cursor.execute('SELECT * FROM theater WHERE theaterCd=?', (theaterCd,))
        apiInfo = cursor.fetchone()
    
        if apiInfo is not None:    
            cursor.execute('SELECT DISTINCT movieIdx FROM ticket WHERE theaterCd=? AND statusId=?', (theaterCd, DUMMY_ID,))
            movieIdxRawList = cursor.fetchall()

            for movieIdxRaw in movieIdxRawList:
                movieIdx = movieIdxRaw[0]

                movieInfo = getMovieInfo(cursor, movieIdx)
                movieTitle = movieInfo['movieTitle']
                movieReleaseDate = movieInfo['movieReleaseDate']

                cursor.execute('SELECT DISTINCT ticketDate FROM ticket WHERE theaterCd=? AND movieIdx=? AND statusId=?', (theaterCd, movieIdx, DUMMY_ID,))
                ticketDateRawList = cursor.fetchall()

                for ticketDateRaw in ticketDateRawList:
                    ticketDate = ticketDateRaw[0]

                    if moment.date(ticketDate, 'YYYYMD') >= movieReleaseDate:           
                        cursor.execute('SELECT DISTINCT ticketTime FROM ticket WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND statusId=?', \
                                       (theaterCd, movieIdx, ticketDate, DUMMY_ID,))
                        ticketTimeRawList = cursor.fetchall()
                        ticketTimeList = sorted([ticketTimeRaw[0] for ticketTimeRaw in ticketTimeRawList])

                        statusId = sendTweet(apiInfo, (movieTitle, ticketDate, ticketTimeList))
                        
                        if not statusId:
                            continue
                        
                        for ticketTime in ticketTimeList:
                            cursor.execute('UPDATE ticket SET statusId=? WHERE theaterCd=? AND movieIdx=? AND ticketDate=? AND ticketTime=?', \
                                           (statusId, theaterCd, movieIdx, ticketDate, ticketTime))
                            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()