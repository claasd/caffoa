from typing import Optional

from caffoa.converter import is_primitive, parse_type
from caffoa.model import BodyConfig
from caffoa.object_parser import BaseObjectParser


class ContentParser:
    def __init__(self, known_types: dict, prefix: str, suffix: str):
        self.known_types = known_types
        self.suffix = suffix
        self.prefix = prefix

    def parse_content_list(self, content: dict, one_of_schemas: dict):
        schema = self.get_schema(content)
        if schema is None:
            return None
        if "$ref" in schema:
            typename = schema["$ref"].split('/')[-1]
            if typename in one_of_schemas:
                schema = one_of_schemas[typename]

        if "oneOf" in schema:
            if "discriminator" not in schema:
                raise Warning()
            discriminator = schema["discriminator"]
            pre_mapping = dict()
            for e_value, e_type in discriminator.get("mapping", dict()).items():
                pre_mapping[e_type] = e_value
            names = list()
            mapping = dict()
            for element in schema["oneOf"]:
                if "$ref" not in element:
                    raise Warning("Cannot have oneOf without ref types")
                ref = element["$ref"]
                name = self.name_for_ref(ref)
                names.append(name)
                if ref in pre_mapping:
                    map_name = pre_mapping[ref]
                else:
                    map_name = ref.split('/')[-1]
                mapping[map_name] = name
            config = BodyConfig(names)
            config.mapping = mapping
            config.discriminator = discriminator["propertyName"]
            return config

        return BodyConfig([self.parse_element(schema)])

    def parse_content_string(self, content: dict):
        schema = self.get_schema(content)
        if schema is None:
            return None
        return self.parse_element(schema)

    def parse_element(self, schema: dict):
        if "$ref" in schema:
            return self.name_for_ref(schema["$ref"])
        if "type" in schema and is_primitive(schema["type"]):
            return parse_type(schema)
        if "type" in schema and schema["type"].lower() == "array":
            if "$ref" in schema["items"]:
                name = self.name_for_ref(schema["items"]["$ref"])
                return f"IEnumerable<{name}>"
            if "type" in schema["items"] and is_primitive(schema["items"]["type"]):
                type = parse_type(schema["items"])
                return f"IEnumerable<{type}>"
            raise Warning("array with complex type that is not a reference")

        raise Warning(
            "complex type. Only array, ref or basic types are supported.")

    @staticmethod
    def get_schema(content: dict) -> Optional[dict]:
        if "content" in content:
            content = content["content"]
            keys = list(content.keys())
            if len(keys) > 1:
                raise Warning(
                    f"multiple possible responses")
            type = str(keys[0])
            if type.lower() != "application/json":
                raise Warning(
                    f"type {type}. Only application/json is currently supported for")
            try:
                schema = content[type]['schema']
                return schema
            except KeyError:
                raise Warning(
                    f"type {type}. no schema found")
        return None

    def name_for_ref(self, ref):
        name = BaseObjectParser(self.prefix, self.suffix).class_name_from_ref(ref)
        if name in self.known_types:
            return dict(self.known_types[name])["type"]
        return name
