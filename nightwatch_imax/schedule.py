# -*- coding: utf-8 -*-
import decimal
import json
import logging
import re

import arrow
import boto3
from boto3.dynamodb.conditions import Key

MOVIE_CODE_PATTERN = re.compile("popupSchedule\('.*','.*','(\d\d:\d\d)','\d*','\d*', '(\d*)', '\d*', '\d*',")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


class ScheduleInfo:
    id = ''
    raw_data = ''

    def __init__(self, schedule_id, raw_data, theater_code, date, movie_code, time, created_at=None):
        self.id = schedule_id
        self.raw_data = str(raw_data)
        self.theater_code = theater_code
        self.date = date
        self.movie_code = movie_code
        self.time = time
        self.created_at = created_at

    def __repr__(self) -> str:
        return self.id

    def is_valid(self):
        return self.id is not ''

    def is_imax_schedule(self):
        return u'아이맥스' in self.raw_data or 'imax' in self.raw_data.lower()


def create_schedule_info(theater_code, date, raw_data):
    schedule_id = ''
    movie_code = ''
    time = ''

    movie_info = MOVIE_CODE_PATTERN.search(raw_data)

    if movie_info is None:
        logger.warning('Wrong schedule_info : %s', raw_data)
    else:
        time = movie_info.group(1).replace(':', '')
        movie_code = movie_info.group(2)
        schedule_id = '{}.{}.{}.{}'.format(theater_code, date, movie_code, time)

    return ScheduleInfo(schedule_id, raw_data, theater_code, date, movie_code, time)


def parse_schedule_info(json_str):
    data = json.loads(json_str)

    return ScheduleInfo(
        schedule_id=data['id'],
        raw_data=data['raw_data'],
        theater_code=data['theater_code'],
        movie_code=data['movie_code'],
        date=data['date'],
        time=data['time'],
        created_at=data['created_at']
    )


def save_schedule_list(schedule_list):
    table = boto3.resource('dynamodb').Table('nightwatch-imax-raw-data')

    created_at = arrow.utcnow().timestamp
    expire_at = arrow.utcnow().shift(minutes=+30).timestamp

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


def get_latest_schedule_list(minute):
    table = boto3.resource('dynamodb').Table('nightwatch-imax-raw-data')

    raw_data = []

    created_from = arrow.utcnow().shift(minutes=-minute).timestamp
    filter_expression = Key('created_at').gte(created_from)

    response = table.scan(
        FilterExpression=filter_expression
    )

    for item in response['Items']:
        data = json.dumps(item, cls=DecimalEncoder)
        raw_data.append(parse_schedule_info(data))

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=filter_expression,
            ExclusiveStartKey=response['LastEvaluatedKey']
        )

        for item in response['Items']:
            data = json.dumps(item, cls=DecimalEncoder)
            raw_data.append(parse_schedule_info(data))

    return raw_data


logger = logging.getLogger()
logger.setLevel(logging.INFO)
