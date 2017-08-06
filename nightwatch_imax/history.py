# -*- coding: utf-8 -*-
import json
import logging

import arrow
import boto3
from boto3.dynamodb.conditions import Key

from nightwatch_imax.schedule import DecimalEncoder


class History:
    id = ''

    def __init__(self, history_id, raw_data, message_result, expire_at=None, created_at=None):
        self.id = history_id
        self.raw_data = str(raw_data)
        self.message_result = str(message_result)
        self.expire_at = expire_at
        self.created_at = created_at


def parse_history(json_str):
    data = json.loads(json_str)

    return History(
        history_id=data['id'],
        raw_data=data['raw_data'],
        message_result=data['message_result'],
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


def save_history_list(history_list, expire_at):
    table = boto3.resource('dynamodb').Table('nightwatch-imax-history')

    created_at = arrow.utcnow().timestamp

    with table.batch_writer() as batch:
        for history in history_list:
            batch.put_item(Item={'id': history.id,
                                 'raw_data': history.raw_data,
                                 'message_result': history.message_result,
                                 'created_at': created_at,
                                 'expire_at': expire_at})

            logger.debug('Saved : %s', history.id)


logger = logging.getLogger()
logger.setLevel(logging.INFO)
