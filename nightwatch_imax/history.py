# -*- coding: utf-8 -*-
import json
import logging

import arrow
import boto3
from boto3.dynamodb.conditions import Key

from nightwatch_imax.schedule import DecimalEncoder


class History:
    id = ''

    def __init__(self, history_id, message_data, schedule_data, expire_at, created_at, message_id=None):
        self.id = history_id
        self.schedule_data = str(schedule_data)
        self.message_data = str(message_data)
        self.expire_at = expire_at
        self.created_at = created_at
        self.message_id = message_id


def parse_history(json_str):
    data = json.loads(json_str)

    return History(
        history_id=data['id'],
        schedule_data=data['schedule_data'],
        message_data=data['message_data'],
        expire_at=data['expire_at'],
        created_at=data['created_at']
    )


def get_history_list(weeks=8):
    table = boto3.resource('dynamodb').Table('nightwatch-imax-history')

    history_list = []

    created_at = arrow.utcnow().shift(weeks=+weeks).timestamp
    filter_expression = Key('created_at').lte(created_at)

    response = table.scan(
        FilterExpression=filter_expression
    )

    for item in response['Items']:
        data = json.dumps(item, cls=DecimalEncoder)
        history_list.append(parse_history(data))

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=filter_expression,
            ExclusiveStartKey=response['LastEvaluatedKey']
        )

        for item in response['Items']:
            data = json.dumps(item, cls=DecimalEncoder)
            history_list.append(parse_history(data))

    return [history.id for history in history_list]


logger = logging.getLogger()
logger.setLevel(logging.INFO)
