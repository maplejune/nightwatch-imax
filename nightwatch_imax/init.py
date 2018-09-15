# -*- coding: utf-8 -*-
from pymongo import MongoClient, DESCENDING, HASHED

if __name__ == "__main__":
    schedule_collection = MongoClient().nightwatch_imax.schedules
    schedule_collection.create_index("id")
    schedule_collection.create_index([("collected_at", DESCENDING)])
    schedule_collection.create_index([("collected_at", DESCENDING), ("reported", DESCENDING)])
    schedule_collection.create_index([("theater_code", DESCENDING), ("date", DESCENDING)])
