# -*- coding: utf-8 -*-
import decimal
import json

import arrow
import boto3
import requests
from boto3.dynamodb.conditions import Key
from bs4 import BeautifulSoup


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

    def __init__(self, data):
        self.id = data.id
        self.created_at = data.created_at
        self.expire_at = data.expire_at
        self.raw_data = data.raw_data
        self.theater_code = data.theater_code
        self.date = data.date
        self.movie_code = data.movie_code
        self.time = data.time

    def is_valid(self):
        return self.id is not ''


class MovieInfo:
    id = ''

    def __init__(self, movie_code, name, release_date, is_imax):
        self.id = movie_code
        self.name = name
        self.release_date = release_date
        self.is_imax = is_imax

    def is_imax(self):
        return self.is_imax


def get_latest_raw_data():
    table = boto3.resource('dynamodb').Table('nightwatch-imax-raw-data')

    raw_data = []

    created_from = arrow.utcnow().shift(minutes=-5).timestamp
    filter_expression = Key('created_at').gte(created_from)

    response = table.scan(
        FilterExpression=filter_expression
    )

    for item in response['Items']:
        data = json.dumps(item, indent=4, cls=DecimalEncoder)
        raw_data.append(ScheduleInfo(data))

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=filter_expression,
            ExclusiveStartKey=response['LastEvaluatedKey']
        )

        for item in response['Items']:
            data = json.dumps(item, indent=4, cls=DecimalEncoder)
            raw_data.append(ScheduleInfo(data))

    return raw_data


def get_movie_info(movie_code):
    movie_info_url = 'http://m.cgv.co.kr/WebApp/MovieV4/movieDetail.aspx?cgvCode={}'.format(movie_code)
    movie_info_response = requests.get(movie_info_url).text

    soup = BeautifulSoup(movie_info_response, 'html.parser')

    name_soup = soup.find('strong', 'tit')
    name = name_soup.text

    release_date_soup = soup.find('span', 'mi_openday')
    release_date = arrow.get(release_date_soup.text, 'YYYY.MM.DD').format('YYYYMMDD')

    is_imax_soup = soup.find('img', alt='IMAX')
    is_imax = is_imax_soup is not None

    return MovieInfo(movie_code, name, release_date, is_imax)


print(get_movie_info(20013221))
