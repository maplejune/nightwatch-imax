# -*- coding: utf-8 -*-
import re
import requests

schedule_response = requests.get("http://m.cgv.co.kr/Schedule/?tc=0074&t=T&ymd=20170719&src=").text

schedule_pattern = re.compile("var ScheduleDateData = \[(.*)\]", re.MULTILINE)
schedule = schedule_pattern.search(schedule_response).group(1).encode().decode("unicode-escape")

date_pattern = re.compile("getMovieSchedule\('(\d{8})',")
dates = date_pattern.findall(schedule)

date_response = requests.post("http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx", data={"theaterCd": "0074", "playYMD": "20170720"})

print(dates)
print(date_response.text)
