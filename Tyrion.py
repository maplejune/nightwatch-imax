#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import datetime, re

class Schedule:
	def __init__(self, data):
		data = re.findall("'(.*?)'", data)
		self.code = data[5]
		self.movieTitle = data[0]
		self.movieIdx = data[6]
		self.playYMD = data[7]
		self.playTime = data[2]
		self.remainingSeat = data[3]
		self.maxSeat = data[4]

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

for theaterCd in ['0074', '0013', '0014']:
	for playYMD in getDateRange():
		for timelist in getTimelist(theaterCd, playYMD):
			if isImaxMovieTimelist(timelist):
				schedules = [Schedule(rawData['href']) for rawData in timelist.find_all('a')]
				for schedule in schedules:
					print theaterCd, schedule.movieTitle, schedule.playYMD, schedule.playTime
