#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import logging, sqlite3, datetime, re, time
from logging import handlers
import pigeon

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

	def getNewPlaytime(self):
		cur.execute(SELECT_QUERY, self.getSelectParams())
		prevWildfire = cur.fetchone()
		
		if prevWildfire is None:
			cur.execute(INSERT_QUERY, self.getInsertParams())
			con.commit()
			prevPlaytime = ''
		else:
			prevPlaytime = prevWildfire[0]
		
		return [playtime for playtime in self.playTime.split(',') if playtime not in prevPlaytime.split(',')]
	
	def updatePlaytime(self):
		cur.execute(UPDATE_QUERY, self.getUpdateParams())
		con.commit()

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

def getPigeon(theaterCd):
	cur.execute('SELECT * FROM blackwater WHERE theater_code=?', (theaterCd,))
	return pigeon.Pigeon(cur.fetchone())

def watchBegins():
	for theaterCd in ['0074', '0013', '0014']:
		pigeon = getPigeon(theaterCd)
		for playYMD in getDateRange():
			time.sleep(1)
			for timelist in getTimelist(theaterCd, playYMD):
				if isImaxMovieTimelist(timelist):
					wildfire = Wildfire(theaterCd, [Schedule(rawData['href']) for rawData in timelist.find_all('a')])
					if wildfire.isReady:
						newPlaytime = wildfire.getNewPlaytime()
						if len(newPlaytime) > 0:
							pigeon.send(wildfire, newPlaytime)
							logger.debug('Wildfire : %s %s %s %s %s %s' % wildfire.getInsertParams())
							time.sleep(1)
					wildfire.updatePlaytime()
					logger.debug('Check : %s %s' % (theaterCd, playYMD))
					
if __name__ == "__main__":
	logger = logging.getLogger('nightwatch-imax')
	logger.setLevel(logging.DEBUG)
	handler = handlers.RotatingFileHandler('/data/script/nightwatch-imax/logs/nightwatch-imax.log', maxBytes=5*1024*1024, backupCount=5)
	logger.addHandler(handler)
	formatter = logging.Formatter('%(asctime)s %(message)s', '%Y-%m-%d %H:%M')
	handler.setFormatter(formatter)

	con = sqlite3.connect('/data/script/nightwatch-imax/tyrion.db')
	cur = con.cursor()

	try:
		watchBegins()
	except Exception, e:
		logger.error(e)	

	con.close()
