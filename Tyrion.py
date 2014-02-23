#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import datetime, re

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
	def __init__(self, schedules):
		if len(schedules) > 0:
			self.isReady = True
			schedule = schedules[0]
			self.movieCd = schedule.movieCd
			self.movieTitle = schedule.movieTitle
			self.scheduleCd = schedule.scheduleCd
			self.playYMD = schedule.playYMD
			self.playTime = ','.join([s.playTime for s in schedules])
		else:
			self.isReady = False

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

def getScheduleInfo(schedules):
	if schedules.length > 0:
		return 

for theaterCd in ['0074', '0013', '0014']:
	for playYMD in getDateRange():
		for timelist in getTimelist(theaterCd, playYMD):
			if isImaxMovieTimelist(timelist):
				wildfire = Wildfire([Schedule(rawData['href']) for rawData in timelist.find_all('a')])
				
				print theaterCd, wildfire.movieCd, wildfire.scheduleCd, wildfire.playYMD, wildfire.movieTitle, wildfire.playTime 
