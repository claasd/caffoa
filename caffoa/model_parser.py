import logging
from typing import Tuple, Optional, List, Set
import re

from prance import ResolvingParser

from caffoa.converter import parse_type, to_camelcase, is_primitive
from caffoa.model import ModelData, MemberData
from caffoa.object_parser import ObjectParser


class ModelParser:
    def __init__(self):
        self.prefix = ""
        self.suffix = ""
        self.known_types = dict()
        self.excludes = list()
        self.includes = list()

    def parse(self, parser: ResolvingParser) -> List[ModelData]:
        schemas = parser.specification["components"]["schemas"]
        self.parse_simple_types(schemas)
        return self.parse_objects(schemas)

    def parse_simple_types(self, schemas: dict):
        for class_name, schema in schemas.items():
            if class_name in self.excludes:
                continue
            if len(self.includes) > 0 and class_name not in self.includes:
                continue
            if "type" in schema and is_primitive(schema["type"]):
                class_name = self.class_name(class_name)
                self.known_types[class_name] = schema

    def parse_objects(self, schemas: dict) -> List[ModelData]:
        objects = list()
        for name, schema in schemas.items():
            if self.class_name(name) in self.known_types:
                continue
            if name in self.excludes:
                continue
            if len(self.includes) > 0 and name not in self.includes:
                continue
            objects.append(ObjectParser(name, self.prefix, self.suffix, self.known_types).parse(schema))
        return objects

    def class_name(self, name):
        return self.prefix + to_camelcase(name) + self.suffix
