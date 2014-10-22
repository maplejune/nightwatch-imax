#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests, moment
import re

TICKET_FORMAT = re.compile(r"popupSchedule\('(.*)','(.*)','(\d\d:\d\d)','\d*','\d*', '\d*', '(\d*)', '(\d*)',")

for theaterCd in ['0074']:
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
                            print movieTitle, ticketType, ticketTime, movieIdx, ticketDate
