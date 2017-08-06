# -*- coding: utf-8 -*-
import logging
import os
import re

import arrow
import requests
from bs4 import BeautifulSoup

from nightwatch_imax.movie import is_imax_movie
from nightwatch_imax.schedule import create_schedule_info, save_schedule_list


def is_cgv_online():
    try:
        health_check = requests.get('http://m.cgv.co.kr')
        return health_check.status_code == 200
    except Exception as e:
        logger.error(e)
        return False


def get_date_list(theater_code):
    today = arrow.now('Asia/Seoul').format('YYYYMMDD')

    date_list_url = 'http://m.cgv.co.kr/Schedule/?tc={}&t=T&ymd={}&src='.format(theater_code, today)
    date_list_response = requests.get(date_list_url).text

    date_list_pattern = re.compile('var ScheduleDateData = \[(.*)\]', re.MULTILINE)
    date_list = date_list_pattern.search(date_list_response).group(1).encode().decode('unicode-escape')

    date_pattern = re.compile('getMovieSchedule\(\'(\d{8})\',')
    dates = date_pattern.findall(date_list)

    logger.info('Targets : %s %s', theater_code, dates)

    return dates


def get_schedule_list(theater_code):
    all_schedule_list = []

    for date in get_date_list(theater_code):
        logger.info('Target : %s %s', theater_code, date)

        schedule_url = 'http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx'
        schedule_response = requests.post(schedule_url, data={'theaterCd': theater_code, 'playYMD': date}).text
        soup = BeautifulSoup(schedule_response, 'html.parser')

        schedule_list = []
        for time_list in soup.find_all('ul', 'timelist'):
            schedule_list.extend(time_list.find_all('li'))

        all_schedule_list.extend(
            [create_schedule_info(theater_code, date, str(raw_data)) for raw_data in schedule_list])

    return list(filter(
        lambda schedule: schedule.is_valid() and schedule.is_imax_schedule() and is_imax_movie(schedule.movie_code),
        all_schedule_list
    ))


def watcher_lambda_handler(event, context):
    if not is_cgv_online():
        raise Exception('Cannot connect CGV server!')

    theater_code = os.environ['theater_code']
    schedule_list = get_schedule_list(theater_code)

    save_schedule_list(schedule_list)

    return theater_code


logger = logging.getLogger()
logger.setLevel(logging.INFO)

save_schedule_list(get_schedule_list('0013'))
