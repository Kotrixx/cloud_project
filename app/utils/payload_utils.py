from datetime import datetime
from typing import Union

from fastapi import HTTPException
from starlette import status


def extract_value(data: dict, path: list[Union[str, int]]):
    """
    Extracts a value from the selected dictionary, given a path to the value.
    :param data: dictionary to traverse.
    :param path: list of keys to traverse the dictionary.
    :return: value at the end of the path.
    """
    value = data
    for key in path:
        if isinstance(value, list):
            value = value[key]
        elif isinstance(value, dict):
            value = value.get(key)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "Invalid path or data structure"}
            )
    return value


def convert_dtype(value: str, dtype: str) -> Union[str, float, int]:
    """
    Converts the value to the specified data type.
    :param value: value to convert.
    :param dtype: data type to convert the value to.
    :return: converted value.
    """
    if dtype == "string":
        return str(value)
    elif dtype == "float":
        return float(value)
    elif dtype == "int":
        return int(value)
    else:
        raise ValueError("Invalid data type")


def get_mapped_value(data: dict, mapping: list[Union[str, int]], dtype: str) -> Union[str, float, int]:
    """
    Gets the value from the specified dictionary, given a mapping path, returning with a specified data type.
    :param data: dictionary to traverse.
    :param mapping: list of keys to traverse the dictionary.
    :param dtype: data type to return the value as.
    :return: value at the end of the path, corresponding to the data type specified.
    """
    value = extract_value(data, mapping)
    return convert_dtype(value, dtype)


def get_timestamp(data: dict, timestamp_mapping: list[Union["str", int]], dt_fmt: str) -> datetime:
    """
    Gets the datetime value of the timestamp for the specified dictionary, based on the mapping path and format provided.
    :param data: dictionary to traverse.
    :param timestamp_mapping: list of keys to traverse the dictionary.
    :param dt_fmt: format of the datetime string.
    :return: datetime object corresponding to the timestamp.
    """
    timestamp = extract_value(data, timestamp_mapping)
    return datetime.strptime(timestamp, dt_fmt)
