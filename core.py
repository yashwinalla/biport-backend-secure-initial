from fastapi import HTTPException
import jwt
import json
import functools
from sqlalchemy.exc import SQLAlchemyError
from app.core import logger
from app.core.enums import ImportantKeys
import base64


def log_exceptions(func):
    """ Decorator to log exceptions and return proper HTTP responses. """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error occurred.")
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired.")
            raise HTTPException(status_code=401, detail="Token has expired")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    return wrapper


def encoding(data_list):
    if not data_list:
        return None
    for data in data_list:
        data[ImportantKeys.PASSWORD.value] = base64.b64encode(data.get(ImportantKeys.PASSWORD.value,"").encode("utf-8")).decode("utf-8")
    data = json.dumps(data_list)
    return data


def decoding(data_list):
    if not data_list:return None
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    data_list=json.loads(data_list)
    for data in data_list:
        data[ImportantKeys.PASSWORD.value]=base64.b64decode(data.get(ImportantKeys.PASSWORD.value,"")).decode("utf-8")
    return data_list