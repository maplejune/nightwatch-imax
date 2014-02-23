#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import sqlite3, datetime, re

con = sqlite3.connect('tyrion.db')
cur = con.cursor()

SELECT_QUERY = 'SELECT play_time FROM wildfire WHERE theater_code=? AND movie_code=? AND schedule_code=? AND play_ymd=?'	
INSERT_QUERY = 'INSERT INTO wildfire (theater_code, movie_code, schedule_code, play_ymd, movie_title, play_time) VALUES (?, ?, ?, ?, ?, ?)'
UPDATE_QUERY = 'UPDATE wildfire SET play_time=? WHERE theater_code=? AND movie_code=? AND schedule_code=? AND play_ymd=?' 

class Schedule:
	def __init__(self, data):
		data = re.findall("'(.*?)'", data)
		self.scheduleCd = data[5]
		self.movieTitle = data[0]
		self.movieCd = data[6]
		self.playYMD = data[7]
		self.playTime = data[2]
		self.remainingSeat = data[3]
		self.maxSeat = data[4]

class Wildfire:
	def __init__(self, theaterCd, schedules):
		if len(schedules) > 0:
			self.isReady = True
			schedule = schedules[0]
			self.theaterCd = theaterCd
			self.movieCd = schedule.movieCd
			self.movieTitle = schedule.movieTitle
			self.scheduleCd = schedule.scheduleCd
			self.playYMD = schedule.playYMD
			self.playTime = ','.join([s.playTime for s in schedules])
		else:
			self.isReady = False

	def getSelectParams(self):
		return (self.theaterCd, self.movieCd, self.scheduleCd, self.playYMD,) 
	
	def getInsertParams(self):
		return (self.theaterCd, self.movieCd, self.scheduleCd, self.playYMD, self.movieTitle, self.playTime,) 

	def getUpdateParams(self):	
		return (self.playTime, self.theaterCd, self.movieCd, self.scheduleCd, self.playYMD,) 

def getTimelist(theaterCd, playYMD):
	data = {'theaterCd':theaterCd, 'playYMD':playYMD}
	response = requests.post('http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx', data)
	soup = BeautifulSoup(response.text)
	return soup.find_all("ul", "timelist")

def getDateRange():
	base = datetime.datetime.today()
	return [(base + datetime.timedelta(days=x)).strftime('%Y%m%d') for x in range(0,25)]

def isImaxMovieTimelist(timelist):
	r = re.search("'(.*?)'", str(timelist))
	return True if bool(r) and r.group().upper().find('IMAX') != -1 else False 

def getPrevPlaytime(wildfire):
	cur.execute(SELECT_QUERY, wildfire.getSelectParams())
	prevWildfire = cur.fetchone()

	if prevWildfire is None:
		cur.execute(INSERT_QUERY, wildfire.getInsertParams())
		con.commit()
		prevPlaytime = wildfire.playTime
	else:
		prevPlaytime = prevWildfire[0]
	
	return prevPlaytime		

def updatePlaytime(wildfire):
	cur.execute(UPDATE_QUERY, wildfire.getUpdateParams())
	con.commit()

def getNewPlaytime(prevPlaytime, currPlaytime):
	return [playtime for playtime in currPlaytime.split(',') if playtime not in prevPlaytime.split(',')]

STATIC_STR = '%s %s %s %s'
def writeTweet(wildfire, playtime):
	print STATIC_STR % (wildfire.movieTitle, wildfire.playYMD[4:6], wildfire.playYMD[6:8], ' '.join([p for p in playtime]))

for theaterCd in ['0074', '0013', '0014']:
	for playYMD in getDateRange():
		for timelist in getTimelist(theaterCd, playYMD):
			if isImaxMovieTimelist(timelist):
				currWildfire = Wildfire(theaterCd, [Schedule(rawData['href']) for rawData in timelist.find_all('a')])
				if currWildfire.isReady:
					newPlaytime = getNewPlaytime(getPrevPlaytime(currWildfire), currWildfire.playTime)
						
					if len(newPlaytime) > 0:
						writeTweet(currWildfire, newPlaytime)
				updatePlaytime(currWildfire)				

con.close()
