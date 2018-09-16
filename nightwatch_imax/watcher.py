# -*- coding: utf-8 -*-
import logging
import re
import sys

import maya
import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup

from nightwatch_imax.schedule import create_schedule_info


def is_cgv_online():
    try:
        health_check = requests.get('http://m.cgv.co.kr')
        return health_check.status_code == 200
    except Exception as e:
        logging.error(e)
        return False


def get_date_list(theater_code):
    today = maya.now().datetime(to_timezone='Asia/Seoul').strftime('%Y%m%d')

    date_list_url = 'http://m.cgv.co.kr/Schedule/?tc={}&t=T&ymd={}&src='.format(theater_code, today)
    date_list_response = requests.get(date_list_url).text

    date_list_pattern = re.compile('var ScheduleDateData = \[(.*)\]', re.MULTILINE)
    date_list = date_list_pattern.search(date_list_response).group(1).encode().decode('unicode-escape')

    date_pattern = re.compile('getMovieSchedule\(\'(\d{8})\',')
    dates = date_pattern.findall(date_list)

    logging.info('Targets : %s %s', theater_code, dates)

    return dates


def get_schedule_list(theater_code):
    schedule_list = []

    for date in get_date_list(theater_code):
        logging.info('Target : %s %s', theater_code, date)

        schedule_url = 'http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx'
        schedule_response = requests.post(schedule_url, data={'theaterCd': theater_code, 'playYMD': date}).text
        soup = BeautifulSoup(schedule_response, 'html.parser')

        for time_list in soup.find_all('ul', 'timelist'):
            schedule_list.extend(
                [create_schedule_info(theater_code, date, str(schedule)) for schedule in time_list.find_all('li')]
            )

    return schedule_list


def watch(theater_code):
    if not is_cgv_online():
        raise Exception('Cannot connect CGV server!')

    for schedule in get_schedule_list(theater_code):
        if schedule.is_valid() and schedule.is_imax_schedule() and schedule_db.find_one({"id": schedule.id}) is None:
            schedule_db.insert_one(schedule.dict())
            logging.info('new schedule : %s', schedule)
        else:
            logging.info('detected schedule : %s', schedule)


schedule_db = MongoClient().nightwatch_imax.schedules

if __name__ == "__main__":
    if len(sys.argv) > 1:
        watch(sys.argv[1:][0])
    else:
        print('Use theater code | ex) python watcher.py 0013')
