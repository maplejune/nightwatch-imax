#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests

data = {'theaterCd':'0074', 'playYMD':'20140224'}
response = requests.post('http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx', data)

print response.text
