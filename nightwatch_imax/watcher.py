# -*- coding: utf-8 -*-
import re
import requests

date_list_response = requests.get("http://m.cgv.co.kr/Schedule/?tc=0074&t=T&ymd=20170719&src=").text

date_list_pattern = re.compile("var ScheduleDateData = \[(.*)\]", re.MULTILINE)
date_list = date_list_pattern.search(date_list_response).group(1).encode().decode("unicode-escape")

date_pattern = re.compile("getMovieSchedule\('(\d{8})',")
dates = date_pattern.findall(date_list)

print(dates)

schedule_response = requests.post("http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx", data={"theaterCd": "0074", "playYMD": "20170720"})

print(schedule_response.text)
