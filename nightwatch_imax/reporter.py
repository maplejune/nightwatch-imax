# -*- coding: utf-8 -*-
import logging
import os
from collections import Counter, defaultdict

from twython import Twython

from nightwatch_imax.history import get_history_list
from nightwatch_imax.schedule import get_latest_schedule_list


def get_latest_raw_data():
    return list(filter(
        lambda _schedule: _schedule.is_valid() and _schedule.is_imax_schedule(),
        get_latest_schedule_list(minute=15)
    ))


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

    for schedule in target_list:
        message_id = '{}.{}'.format(schedule.theater_code, schedule.movie_code)
        message_data[message_id].add(schedule.date)

    print(message_data)
    print('%s %s월 %s일 예매가 열린 것 같아요. 10분간 더 살펴보고 확정적이면 다시 알려드릴게요!')


def report_solid_detection(schedule_list, detection_list):
    print('%s %s월 %s일 예매가 열렸습니다. %s 예매가능!')


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

report_initial_detection(a, initial_detection_list)
