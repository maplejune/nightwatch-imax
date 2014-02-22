#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

data = {'theaterCd':'0074', 'playYMD':'20140224'}
response = requests.post('http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx', data)
soup = BeautifulSoup(response.text)
timelists = soup.find_all("ul", "timelist")

def isImaxMovieTimelist(timelist):
	return str(timelist).find('아이맥스') != -1

for timelist in timelists:
	if isImaxMovieTimelist(timelist):
		print timelist
