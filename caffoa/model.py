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

    def __str__(self):
        return f"{self.operation} {self.path} -> {self.parameters}"


class Parameter:
    def __init__(self, name: str, type: str, desc: str):
        self.desc = desc
        self.type = type
        self.name = name
