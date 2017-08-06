# -*- coding: utf-8 -*-
import logging
import os
from collections import Counter, defaultdict

import arrow
from twython import Twython

from nightwatch_imax.history import get_history_list, History, save_history_list
from nightwatch_imax.movie import get_movie_info
from nightwatch_imax.schedule import get_latest_schedule_list


def get_latest_raw_data():
    return list(filter(
        lambda _schedule: _schedule.is_valid() and _schedule.is_imax_schedule(),
        get_latest_schedule_list(minute=15)
    ))


def get_unique_raw_data(schedule_list):
    unique_list = list()

    id_list = set()
    for schedule in schedule_list:
        if schedule.id not in id_list:
            id_list.add(schedule.id)
            unique_list.append(schedule)

    return unique_list


def get_detection_list(schedule_list, condition):
    schedule_counter = Counter([schedule.id for schedule in schedule_list])

    for schedule_id, count in schedule_counter.copy().items():
        if not condition(count):
            del (schedule_counter[schedule_id])

    candidate_list = list(schedule_counter.keys())

    if len(candidate_list) == 0:
        return []

    return list(filter(
        lambda candidate: candidate not in get_history_list(),
        candidate_list
    ))


def report_initial_detection(schedule_list, detection_list):
    target_list = list(filter(
        lambda _schedule: _schedule.id in detection_list,
        schedule_list
    ))

    message_data = defaultdict(set)
    message_result = dict()

    for schedule in target_list:
        message_id = '{}.{}'.format(schedule.theater_code, schedule.movie_code)
        message_data[message_id].add(schedule.date)

    for data_id, data in message_data.items():
        theater_code, movie_code = data_id.split('.')

        movie_info = get_movie_info(movie_code)
        date_list = sorted((list(data)))

        message = '<{}> [{}] 예매가 열린 것 같아요. 10분간 더 살펴보고 확정적이면 다시 알려드릴게요!'.format(
            movie_info.name,
            ', '.join([arrow.get(date, 'YYYYMMDD').format('M월 D일') for date in date_list])
        )

        result = report(theater_code, message)
        message_result.setdefault(data_id, result)

    history_list = []
    expire_at = arrow.utcnow().shift(minutes=+10).timestamp

    for schedule in target_list:
        message_id = '{}.{}'.format(schedule.theater_code, schedule.movie_code)
        history_list.append(History(schedule.id, schedule.raw_data, message_result[message_id]))

    save_history_list(history_list, expire_at)


def report_solid_detection(schedule_list, detection_list):
    target_list = list(filter(
        lambda _schedule: _schedule.id in detection_list,
        schedule_list
    ))

    message_data = defaultdict(set)
    message_result = dict()

    for schedule in target_list:
        message_id = '{}.{}.{}'.format(schedule.theater_code, schedule.movie_code, schedule.date)
        message_data[message_id].add(schedule.time)

    for data_id, data in message_data.items():
        theater_code, movie_code, date = data_id.split('.')

        movie_info = get_movie_info(movie_code)
        date_str = arrow.get(date, 'YYYYMMDD').format('M월 D일')
        time_list = sorted((list(data)))

        message = '<{}> {} 예매가 열렸습니다. {} 예매가능!'.format(
            movie_info.name,
            date_str,
            ' '.join([time[:2] + ':' + time[2:] for time in time_list])
        )

        result = report(theater_code, message)
        message_result.setdefault(data_id, result)

    history_list = []
    expire_at = arrow.utcnow().shift(minutes=+10).timestamp

    for schedule in target_list:
        message_id = '{}.{}.{}'.format(schedule.theater_code, schedule.movie_code, schedule.date)
        history_list.append(History(schedule.id, schedule.raw_data, message_result[message_id]))

    save_history_list(history_list, expire_at)


def report(theater_code, message):
    try:
        token = os.environ[theater_code].split(',')
        twitter = Twython(app_key=token[0], app_secret=token[1], oauth_token=token[2], oauth_token_secret=token[3])
        return twitter.update_status(status=message)
    except Exception as e:
        logger.error(e)
        return str(e)


logger = logging.getLogger()
logger.setLevel(logging.INFO)

a = get_latest_raw_data()

initial_detection_list = get_detection_list(a, lambda count: count < 10)
solid_detection_list = get_detection_list(a, lambda count: count > 10)

print(initial_detection_list)
print(solid_detection_list)

b = get_unique_raw_data(a)

report_initial_detection(b, initial_detection_list)
report_solid_detection(b, solid_detection_list)
