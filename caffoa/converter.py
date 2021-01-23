import os

TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


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


def parse_type(schema: dict) -> str:
    format = None
    if "format" in schema:
        format = schema['format'].lower()
    type = schema['type'].lower()
    if type == "string" and format == "uuid":
        return "System.Guid"
    if type == "string" and format == "date-time":
        return "System.DateTime"
    if type == "string" and format == "date":
        return "System.DateTime"
    if type == "integer":
        return "int"
    if type == "number":
        return "double"
    if type == "boolean":
        return "bool"
    return type
