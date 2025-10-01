from __future__ import annotations
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
import redis


db = SQLAlchemy()


def redis_client(config) -> redis.Redis:
    pool = redis.ConnectionPool(
        host=config.get("REDIS_HOST"),
        port=config.get("REDIS_PORT"),
        db=config.get("REDIS_DB"),
        password=config.get("REDIS_PASSWORD"),
        decode_responses=True,
    )
    return redis.Redis(connection_pool=pool) 