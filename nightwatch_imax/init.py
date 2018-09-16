# -*- coding: utf-8 -*-
from pymongo import MongoClient, DESCENDING

if __name__ == "__main__":
    schedule_db = MongoClient().nightwatch_imax.schedules
    schedule_db.create_index("code")
    schedule_db.create_index([("theater_code", DESCENDING), ("date", DESCENDING)])
    schedule_db.create_index([("theater_code", DESCENDING), ("date", DESCENDING), ("reported", DESCENDING)])
