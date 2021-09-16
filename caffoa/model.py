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
        self.imports = set()
        self.description = None
