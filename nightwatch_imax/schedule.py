# -*- coding: utf-8 -*-
import json
import logging
import re

import maya

MOVIE_CODE_PATTERN = re.compile("popupSchedule\('.*','.*','(\d\d:\d\d)','\d*','\d*', '(\d*)', '\d*', '\d*',")


class ScheduleInfo:
    id = ''
    raw_data = ''

    def __init__(self, id, raw_data, theater_code, date, movie_code, time, collected_at):
        self.id = id
        self.raw_data = str(raw_data)
        self.theater_code = theater_code
        self.date = date
        self.movie_code = movie_code
        self.time = time
        self.collected_at = collected_at

    def __repr__(self) -> str:
        return self.id

    def is_valid(self):
        return self.id is not ''

    def is_imax_schedule(self):
        return u'아이맥스' in self.raw_data or 'imax' in self.raw_data.lower()

    def dict(self):
        return {
            'id': self.id,
            'raw_data': self.raw_data,
            'theater_code': self.theater_code,
            'date': self.date,
            'time': self.time,
            'collected_at': self.collected_at,
            'reported': False
        }


def create_schedule_info(theater_code, date, raw_data):
    schedule_id = ''
    movie_code = ''
    time = ''

    movie_info = MOVIE_CODE_PATTERN.search(raw_data)

    if movie_info is None:
        logging.warning('wrong schedule_info : %s', raw_data)
    else:
        time = movie_info.group(1).replace(':', '')
        movie_code = movie_info.group(2)
        schedule_id = '{}.{}.{}.{}'.format(theater_code, date, movie_code, time)

    return ScheduleInfo(schedule_id, raw_data, theater_code, date, movie_code, time, maya.now().epoch)


def parse_schedule_info(json_str):
    data = json.loads(json_str)

    return ScheduleInfo(
        id=data['id'],
        raw_data=data['raw_data'],
        theater_code=data['theater_code'],
        movie_code=data['movie_code'],
        date=data['date'],
        time=data['time'],
        collected_at=data['collected_at']
    )
