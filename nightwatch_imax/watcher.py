# -*- coding: utf-8 -*-
import re
import requests
import moment
from bs4 import BeautifulSoup


def is_cgv_online():
    try:
        health_check = requests.get('http://m.cgv.co.kr')
        return health_check.status_code == 200
    except Exception as e:
        print(e)
        return False


def get_date_list(theater_code):
    today = moment.now().locale('Asia/Seoul').strftime('%Y%m%d')

    date_list_url = 'http://m.cgv.co.kr/Schedule/?tc={}&t=T&ymd={}&src='.format(theater_code, today)
    date_list_response = requests.get(date_list_url).text

    date_list_pattern = re.compile('var ScheduleDateData = \[(.*)\]', re.MULTILINE)
    date_list = date_list_pattern.search(date_list_response).group(1).encode().decode('unicode-escape')

    date_pattern = re.compile('getMovieSchedule\(\'(\d{8})\',')
    dates = date_pattern.findall(date_list)

    return dates


def get_schedule_list(theater_code, date):
    schedule_url = 'http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx'
    schedule_response = requests.post(schedule_url, data={'theaterCd': theater_code, 'playYMD': date}).text
    soup = BeautifulSoup(schedule_response, 'html.parser')

    schedule_list = []

    for time_list in soup.find_all('ul', 'timelist'):
        schedule_list.extend(time_list.find_all('li'))

    return schedule_list


def aws_lambda_handler(event, context):
    if not is_cgv_online():
        return

    theater_codes = ['0074']

    for theater_code in theater_codes:
        date_list = get_date_list(theater_code)

        for date in date_list:
            schedule_list = get_schedule_list(theater_code, date)

            print('{}.{}'.format(theater_code, date))
            print(schedule_list)


aws_lambda_handler('', '')
