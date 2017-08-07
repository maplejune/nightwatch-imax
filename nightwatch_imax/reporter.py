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


def get_detection_list(schedule_list, history_list, condition):
    schedule_counter = Counter([schedule.id for schedule in schedule_list])

    for schedule_id, count in schedule_counter.copy().items():
        if not condition(count):
            del (schedule_counter[schedule_id])

    candidate_list = list(schedule_counter.keys())

    if len(candidate_list) == 0:
        return []

    return list(filter(
        lambda candidate: candidate not in history_list,
        candidate_list
    ))


def report_initial_detection(schedule_list, detection_list):
    target_list = list(filter(
        lambda _schedule: _schedule.id in detection_list,
        schedule_list
    ))

    history_list = list()
    schedule_by_movie = defaultdict(list)

    for schedule in target_list:
        message_id = '{}.{}'.format(schedule.theater_code, schedule.movie_code)
        schedule_by_movie[message_id].append(schedule)

    for message_id, schedule_by_date in sorted(schedule_by_movie.items()):
        theater_code, movie_code = message_id.split('.')

        movie_info = get_movie_info(movie_code)
        date_list = sorted(set([_schedule.date for _schedule in schedule_by_date]))

        message = '<{}> {} 예매가 열린 것 같아요. 10분간 더 살펴보고 확정적이면 다시 알려드릴게요!'.format(
            movie_info.name,
            ', '.join([arrow.get(date, 'YYYYMMDD').format('M월 D일') for date in date_list])
        )

        is_success, response = report(theater_code, message)

        if not is_success:
            logger.error('Report failed - theater_code[%s] message[%s]', theater_code, message)
            continue

        logger.info('Report success - message[%s] response[%s]', message, response)
        history_list.extend([History(_schedule.id, _schedule.raw_data, response) for _schedule in schedule_by_date])

    expire_at = arrow.utcnow().shift(minutes=+10).timestamp
    save_history_list(history_list, expire_at)


def report_solid_detection(schedule_list, detection_list):
    target_list = list(filter(
        lambda _schedule: _schedule.id in detection_list,
        schedule_list
    ))

    history_list = list()
    schedule_by_date = defaultdict(list)

    for schedule in target_list:
        message_id = '{}.{}.{}'.format(schedule.theater_code, schedule.movie_code, schedule.date)
        schedule_by_date[message_id].append(schedule)

    for message_id, schedule_by_time in sorted(schedule_by_date.items()):
        theater_code, movie_code, date = message_id.split('.')

        movie_info = get_movie_info(movie_code)
        date_str = arrow.get(date, 'YYYYMMDD').format('M월 D일')
        time_list = sorted(set([_schedule.time for _schedule in schedule_by_time]))

        message = '<{}> {} 예매가 열렸습니다. {} 예매가능!'.format(
            movie_info.name,
            date_str,
            ' '.join([time[:2] + ':' + time[2:] for time in time_list])
        )

        is_success, response = report(theater_code, message)

        if not is_success:
            logger.error('Report failed - theater_code[%s] message[%s]', theater_code, message)
            continue

        logger.info('Report success - message[%s] response[%s]', message, response)
        history_list.extend([History(_schedule.id, _schedule.raw_data, response) for _schedule in schedule_by_time])

    expire_at = arrow.utcnow().shift(weeks=+8).timestamp
    save_history_list(history_list, expire_at)


def report(theater_code, message):
    try:
        token = os.environ['T' + theater_code].split(',')
        twitter = Twython(app_key=token[0], app_secret=token[1], oauth_token=token[2], oauth_token_secret=token[3])
        return True, twitter.update_status(status=message)
    except Exception as e:
        logging.exception('Something wrong with reporting...')
        return False, e


def reporter_lambda_handler(event, context):
    latest_raw_data = get_latest_raw_data()
    recent_history = get_history_list()

    initial_detection_list = get_detection_list(latest_raw_data, recent_history, lambda count: count < 10)
    solid_detection_list = get_detection_list(latest_raw_data, recent_history, lambda count: count > 10)

    unique_raw_data = get_unique_raw_data(latest_raw_data)

    report_initial_detection(unique_raw_data, initial_detection_list)
    report_solid_detection(unique_raw_data, solid_detection_list)

    return 'initial_detection:{} solid_detection:{}'.format(len(initial_detection_list), len(solid_detection_list))


logger = logging.getLogger()
logger.setLevel(logging.INFO)
