from typing import Optional, List, Set


class MemberData:
    def __init__(self, name):
        self.is_list = False
        self.name = name
        self.typename = None
        self.is_date = False
        self.nullable = False
        self.default_value = None
        self.is_required = False
        self.description = None
        self.enums = None
        self.is_basic_type = True


class ModelData:
    def __init__(self, rawname: str, name: str):
        self.rawname = rawname
        self.name = name
        self.parent = None
        self.properties = list()
        self.imports = list()
        self.description = None


class EndPoint:
    def __init__(self, name, path, operation, parameters: list, documentation: list, needs_content: bool):
        self.name = name
        self.parameters = parameters
        self.operation = operation
        self.path = path
        self.documentation = documentation
        self.needs_content = needs_content
        self.responses = None
        self.body = None

    def __str__(self):
        return f"{self.operation} {self.path} ({self.parameters}) -> {self.responses}"


class Parameter:
    def __init__(self, name: str, type: str, desc: str):
        self.desc = desc
        self.type = type
        self.name = name

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"{self.type} {self.name}"


class Response:
    def __init__(self, code):
        self.code = int(code)
        self.content = None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"{self.code}/{self.content}"


class MethodResult:
    def __init__(self, name: str):
        self.base = name
        self.name = name
        self.code = 200
        self.codes = list()
        self.is_simple = True
