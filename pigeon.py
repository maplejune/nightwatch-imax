#!/usr/bin/python
# -*- coding: utf-8 -*-

import twitter

class Pigeon:
	def __init__(self, data):
		self.name = data[2]
		self.api = twitter.Api(consumer_key=data[3], consumer_secret=data[4], access_token_key=data[5], access_token_secret=data[6])
	def send(self, wildfire, playtime):
		message = u'%s %s월 %s일 예매가 열렸습니다. %s 예매가능! #%s' % (wildfire.movieTitle, 
																		int(wildfire.playYMD[4:6]), 
																		int(wildfire.playYMD[6:8]), 
																		' '.join([p for p in playtime]),
																		self.name)
		self.api.PostUpdate(message)
