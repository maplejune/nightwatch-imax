#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import datetime

def getTimelist(theaterCd, playYMD):
	data = {'theaterCd':theaterCd, 'playYMD':playYMD}
	response = requests.post('http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx', data)
	soup = BeautifulSoup(response.text)
	return soup.find_all("ul", "timelist")

def getDateRange():
	base = datetime.datetime.today()
	return [(base + datetime.timedelta(days=x)).strftime('%Y%m%d') for x in range(0,25)]

def isImaxMovieTimelist(timelist):
	return str(timelist).find('아이맥스') != -1

for theaterCd in ['0074', '0013', '0014']:
	for playYMD in getDateRange():
		for timelist in getTimelist(theaterCd, playYMD):
			if isImaxMovieTimelist(timelist):
				print timelist

