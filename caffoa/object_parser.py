import logging
import re
from typing import Optional, Tuple

from caffoa.converter import to_camelcase, parse_type, is_date
from caffoa.model import ModelData, MemberData, ModelObjectData, ModelInterfaceData


class BaseObjectParser:
    def __init__(self, prefix: str, suffix: str):
        self.suffix = suffix
        self.prefix = prefix

    def name_from_ref(self, param: str):
        if ".yml_schemas_" in param:
            param = param.split(".yml_schemas_")[-1]
        name = param.split('/')[-1]
        return name

    def class_name_from_ref(self, param: str):
        return self.class_name(self.name_from_ref(param))

    def class_name(self, name):
        return self.prefix + to_camelcase(name) + self.suffix


class ObjectParser(BaseObjectParser):
    def __init__(self, raw_name, prefix: str, suffix: str, known_types: dict):
        super().__init__(prefix, suffix)
        self.name = raw_name
        self.known_types = known_types
        self.result = ModelObjectData(self.name, self.class_name(self.name))

    def parse(self, schema: dict) -> ModelData:
        if "allOf" in schema:
            schema, self.result.parent = self.handle_all_of(schema)
        if "oneOf" in schema:
            self.result = ModelInterfaceData(self.name, self.class_name(self.name))
            discriminator = schema.get("discriminator")
            if discriminator:
                self.result.discriminator = to_camelcase(discriminator["propertyName"])
            for element in schema["oneOf"]:
                if "$ref" in element:
                    self.result.children.append(self.class_name_from_ref(element["$ref"]))
                elif "required" in element:
                    pass # this is fine: https://github.com/p1c2u/openapi-spec-validator/issues/27
                else:
                    logging.warning("did not find $ref as child of oneOf")
        elif "properties" in schema:
            required_props = schema.get('required', list())
            for name, data in schema["properties"].items():
                self.result.properties.append(self.create_param(name, data, name in required_props))

        if "description" in schema:
            self.result.description = schema["description"]

        return self.result

    def handle_all_of(self, schema: dict) -> Tuple[dict, Optional[str]]:
        to_generate = None
        parent = None
        for element in schema["allOf"]:
            if "$ref" in element:
                if parent is None:
                    parent = self.class_name_from_ref(element["$ref"])
                else:
                    raise Warning("allOf is implemented as inheritance; cannot have to children with $ref")
            if "type" in element or "properties" in element:
                if to_generate is not None:
                    raise Warning(
                        "allOf is implemented as inheritance; cannot have to children of allOf with direct implementation")
                to_generate = element
        if to_generate is None:
            logging.warning("Creating class without content, no child of allOf is type object")
            to_generate = dict()
        return to_generate, parent

    def create_param(self, name: str, data: dict, required: bool) -> MemberData:
        param = MemberData(name)
        # handle default type references, replace data if so
        if "$ref" in data:
            param.typename = self.class_name_from_ref(data["$ref"])
            if param.typename in self.known_types:
                data = self.known_types[param.typename]

        param.is_required = required
        param.nullable = "nullable" in data and data["nullable"]

        # handle nullable references that are constructed with anyOf
        if "anyOf" in data:
            data = self.handle_any_of(data, name)

        if "description" in data:
            param.description = data["description"]

        if "$ref" in data:
            param.typename, param.default_value = self.handle_ref(data, param.is_required)
            param.nullable = not param.is_required
            param.is_basic_type = False

        elif "type" not in data:
            raise Warning(f"Cannot parse property without type for '{name}' in '{self.name}'")

        elif data["type"] == "array":
            param.typename, param.default_value = self.handle_array(data, name, param.nullable)
            self.result.imports.append("System.Collections.Generic")
            self.result.imports.append("System.Linq")
            param.is_list = True

        elif data["type"] == "object":
            if "properties" in data:
                raise Warning(
                    f"Cannot parse property trees: '{name}' child of '{self.name}' should be declared in own schema directly under 'components'")
            if "additionalProperties" in data:
                param.typename, param.default_value = self.handle_additional_properties(data, param.nullable)
                self.result.imports.append("System.Collections.Generic")
            else:
                raise Warning(
                    f"Cannot nested object without additionalProperties: '{name}' child of '{self.name}'")

        else:
            param.typename, param.default_value = self.handle_default_type(data, param.nullable)
            param.enums = self.handle_enums(name, data)
            if param.enums and None in param.enums.keys():
                param.typename, param.default_value = self.handle_default_type(data, True)
            if param.enums is not None:
                self.result.imports.append("System")
                self.result.imports.append("System.Collections.Immutable")
            param.is_date = is_date(data)
        return param

    def handle_any_of(self, data: dict, name: str):
        anyof = data["anyOf"]
        if len(anyof) != 1:
            raise Warning(f"anyOf with multiple children not supported for '{name}' in '{self.name}'")
        anyof = anyof[0]
        if "$ref" not in anyof:
            raise Warning(f"anyOf child other than $ref not supported for '{name}' in '{self.name}'")
        data["$ref"] = anyof["$ref"]
        typename = self.class_name_from_ref(data["$ref"])
        if typename in self.known_types:
            data = self.known_types[typename]
        return data

    def handle_ref(self, data: dict, required: bool) -> Tuple[str, str]:
        typename = self.class_name_from_ref(data["$ref"])
        if required:
            default_value = f"new {typename}()"
        else:
            default_value = "null"
        return typename, default_value

    def handle_array(self, data: dict, name: str, nullable: bool) -> Tuple[str, str]:
        items = data["items"]
        if "$ref" in items:
            typename = self.class_name_from_ref(items["$ref"])
        elif items["type"] not in ["string", "number", "integer", "boolean"]:
            raise Warning(
                f"Cannot parse array trees: '{name}' child of '{self.name}' should have it's array item declared in own schema directly under 'components'")
        else:
            typename = parse_type(items, nullable)
        return f"ICollection<{typename}>", f"new List<{typename}>()"

    def handle_additional_properties(self, data: dict, nullable: bool) -> Tuple[str, str]:
        props = data['additionalProperties']
        if "$ref" in props:
            typename = self.class_name_from_ref(props["$ref"])
        else:
            typename = parse_type(props, nullable)
        return f"Dictionary<string, {typename}>", f"new Dictionary<string, {typename}>()"

    def handle_default_type(self, data: dict, nullable: bool) -> Tuple[str, str]:
        default_value = None
        if "default" in data:
            default_value = data["default"]
            if type(default_value) is str:
                default_value = f'"{default_value}"'
            elif type(default_value) is bool:
                default_value = "true" if default_value else "false"
            elif default_value is None:
                default_value = "null"
        elif nullable:
            default_value = "null"
        typename = parse_type(data, nullable and default_value == "null")
        return typename, default_value

    def handle_enums(self, name: str, data: dict) -> Optional[dict]:
        if "enum" not in data:
            return None
        enum = data["enum"]
        if len(enum) == 0:
            return None
        typename, _ = self.handle_default_type(data, False)
        if typename not in ["string", "int", "long", "double"]:
            return None

        enums = dict()
        for value in enum:
            name = value
            name = re.sub(r"[^A-Za-z0-9]+", '_', str(name))
            if typename == "string":
                value = f'"{value}"'
            enums[value] = name

        return enums
