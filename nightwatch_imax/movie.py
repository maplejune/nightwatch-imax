# -*- coding: utf-8 -*-
import logging

import arrow
import boto3
import requests
from bs4 import BeautifulSoup


class MovieInfo:
    id = ''

    def __init__(self, movie_code, name, release_date, is_imax):
        self.id = movie_code
        self.name = name
        self.release_date = release_date
        self.is_imax = is_imax

    def __repr__(self) -> str:
        return self.id


MOVIE_INFO_CACHE = {}


def is_imax_movie(movie_code):
    if movie_code is '':
        return False

    return get_movie_info(movie_code).is_imax


def get_movie_info(movie_code):
    if movie_code in MOVIE_INFO_CACHE:
        logger.debug('Cache Hit : %s', movie_code)
        return MOVIE_INFO_CACHE[movie_code]

    table = boto3.resource('dynamodb').Table('nightwatch-imax-movie')
    response = table.get_item(Key={'id': movie_code})

    if 'Item' in response:
        movie_data = response['Item']
        movie_info = MovieInfo(movie_code, movie_data['name'], movie_data['release_date'], movie_data['is_imax'])

        MOVIE_INFO_CACHE[movie_code] = movie_info

        return movie_info

    movie_info_url = 'http://m.cgv.co.kr/WebApp/MovieV4/movieDetail.aspx?cgvCode={}'.format(movie_code)
    movie_info_response = requests.get(movie_info_url).text

    soup = BeautifulSoup(movie_info_response, 'html.parser')

    name_soup = soup.find('strong', 'tit')
    name = name_soup.text

    release_date_soup = soup.find('span', 'mi_openday')
    release_date = arrow.get(release_date_soup.text, 'YYYY.MM.DD').format('YYYYMMDD')

    is_imax_soup = soup.find('img', alt='IMAX')
    is_imax = is_imax_soup is not None

    movie_info = MovieInfo(movie_code, name, release_date, is_imax)
    save_movie_info(movie_info)

    MOVIE_INFO_CACHE[movie_code] = movie_info

    return movie_info


def save_movie_info(movie_info):
    table = boto3.resource('dynamodb').Table('nightwatch-imax-movie')

    table.put_item(
        Item={
            'id': movie_info.id,
            'name': movie_info.name,
            'release_date': movie_info.release_date,
            'is_imax': movie_info.is_imax,
            'created_at': arrow.utcnow().timestamp
        }
    )


logger = logging.getLogger()
logger.setLevel(logging.INFO)
