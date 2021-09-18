import logging
import os
from typing import List, Optional

from caffoa.model import Response, MethodResult


def capitalize_first(data: str) -> str:
    if len(data) > 1:
        return data[0].upper() + data[1:]
    return data


def to_camelcase(s):
    s = s.replace("-", "_")
    return ''.join(capitalize_first(x) or '_' for x in s.split('_'))


def is_date(schema: dict):
    if "format" not in schema or "type" not in schema:
        return False
    return schema['type'] == "string" and schema['format'] == "date"


def is_primitive(type: str):
    return type.lower() in ["string", "integer", "number", "boolean"]


def parse_type(schema: dict, nullable: bool = False) -> str:
    format = None
    if "format" in schema:
        format = schema['format'].lower()
    type = schema['type'].lower()
    if nullable:
        suffix = "?"
    else:
        suffix = ""
    if type == "string" and format == "uuid":
        return f"System.Guid{suffix}"
    if type == "string" and format in ["date-time", "date"]:
        return f"System.DateTime{suffix}"
    if type == "integer" and format == "int64":
        return f"long{suffix}"
    if type == "integer" and format == "uint64":
        return f"ulong{suffix}"
    if type == "integer" and format == "uint32":
        return f"uint{suffix}"
    if type == "integer":
        return f"int{suffix}"
    if type == "number":
        return f"double{suffix}"
    if type == "boolean":
        return f"bool{suffix}"
    if type == "string":
        return "string"  # no nullable suffix for string
    return f"{type}{suffix}"


def get_response_type(responses: List[Response]) -> Optional[MethodResult]:
    type = None
    codes = list()
    if responses is None:
        return None
    for response in responses:
        if 200 <= response.code < 300:
            if type is not None and type != response.content:
                logging.warning("Returning different objects is not supported")
                return None
            type = response.content
            codes.append(response.code)
    if len(codes) == 0:
        return None
    result = MethodResult(type)
    if len(codes) == 1:
        result = MethodResult(type)
        result.code = codes[0]
        return result

    result.name = type + "ResultWrapper"
    result.is_simple = False
    result.codes = codes
    return result
