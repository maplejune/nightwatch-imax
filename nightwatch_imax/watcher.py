# -*- coding: utf-8 -*-
import logging
import os
import re

import arrow
import boto3
import requests
from bs4 import BeautifulSoup

MOVIE_CODE_PATTERN = re.compile("popupSchedule\('.*','.*','(\d\d:\d\d)','\d*','\d*', '(\d*)', '\d*', '\d*',")


class ScheduleInfo:
    id = ''

    def __init__(self, theater_code, date, raw_data):
        self.theater_code = theater_code
        self.date = date
        self.raw_data = raw_data

        movie_info = MOVIE_CODE_PATTERN.search(raw_data)

        if movie_info is None:
            logger.warning('Wrong schedule_info : %s', raw_data)
        else:
            self.time = movie_info.group(1).replace(':', '')
            self.movie_code = movie_info.group(2)
            self.id = '{}.{}.{}.{}'.format(theater_code, date, self.movie_code, self.time)

    def is_valid(self):
        return self.id is not ''


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
    result = []

    for date in get_date_list(theater_code):
        logger.info('Target : %s %s', theater_code, date)

        schedule_url = 'http://m.cgv.co.kr/Schedule/cont/ajaxMovieSchedule.aspx'
        schedule_response = requests.post(schedule_url, data={'theaterCd': theater_code, 'playYMD': date}).text
        soup = BeautifulSoup(schedule_response, 'html.parser')

        schedule_list = []
        for time_list in soup.find_all('ul', 'timelist'):
            schedule_list.extend(time_list.find_all('li'))

        result.extend([ScheduleInfo(theater_code, date, str(raw_data)) for raw_data in schedule_list])

    return list(filter(lambda schedule_info: schedule_info.is_valid(), result))


def save(schedule_list):
    table = boto3.resource('dynamodb').Table('nightwatch-imax-raw-data')

    created_at = arrow.utcnow().timestamp
    expire_at = arrow.utcnow().shift(days=+1).timestamp

    with table.batch_writer(overwrite_by_pkeys=['id', 'created_at']) as batch:
        for schedule_info in schedule_list:
            batch.put_item(Item={'id': schedule_info.id,
                                 'created_at': created_at,
                                 'expire_at': expire_at,
                                 'raw_data': schedule_info.raw_data,
                                 'theater_code': schedule_info.theater_code,
                                 'date': schedule_info.date,
                                 'movie_code': schedule_info.movie_code,
                                 'time': schedule_info.time})

            logger.debug('Saved : %s', schedule_info.id)


def watcher_lambda_handler(event, context):
    if not is_cgv_online():
        raise Exception('Cannot connect CGV server!')

    theater_code = os.environ['theater_code']
    schedule_list = get_schedule_list(theater_code)
    save(schedule_list)

    return theater_code


logger = logging.getLogger()
logger.setLevel(logging.INFO)
