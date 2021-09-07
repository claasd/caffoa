import logging
from typing import Tuple, Optional, List, Set
import re

from prance import ResolvingParser
from prance.util.resolver import RESOLVE_HTTP, RESOLVE_FILES, TRANSLATE_EXTERNAL

from caffoa.converter import parse_type, to_camelcase


class MemberData:
    def __init__(self, name: str, type: str, is_date: bool, nullable: bool, default_value: Optional[str],
                 is_required: bool, description: Optional[str], enums: Optional[str]):
        self.name = name
        self.type = type
        self.is_date = is_date
        self.nullable = nullable
        self.default_value = default_value
        self.is_required = is_required
        self.description = description
        self.enums = enums


class ModelData:
    def __init__(self, rawname: str, name: str, parents: list, properties: List[MemberData], imports: Set[str],
                 description: Optional[str]):
        self.rawname = rawname
        self.name = name
        self.parents = parents
        self.properties = properties
        self.imports = imports
        self.description = description


class SchemaParser:
    def __init__(self, prefix: str, suffix: str, excludes: list):
        self.prefix = prefix
        self.suffix = suffix
        self.known_types = dict()
        self.excludes = excludes

    def parse(self, input_file: str) -> List[ModelData]:
        parser = ResolvingParser(input_file, strict=False, resolve_types=RESOLVE_HTTP | RESOLVE_FILES,
                                 resolve_method=TRANSLATE_EXTERNAL)
        schemas = parser.specification["components"]["schemas"]
        for class_name, schema in schemas.items():
            if ".yml_schemas_" in class_name:
                class_name = class_name.split(".yml_schemas_")[-1]
            print(class_name, schema)
            if class_name in self.excludes:
                continue
            self.parse_simple(class_name, schema)

        objects = list()
        for class_name, schema in schemas.items():
            if self.class_name(class_name) in self.known_types:
                continue
            if class_name in self.excludes:
                continue
            objects.append(self.parse_objects(class_name, schema))
        return objects

    def parse_simple(self, class_name: str, schema: dict):
        if "type" in schema:
            typename = schema["type"]
            if typename in ["string", "integer", "number", "boolean"]:
                class_name = self.class_name(class_name)
                self.known_types[class_name] = schema

    def parse_objects(self, class_name: str, schema: dict, parents=None):
        if parents is None:
            parents = set()
        imports = set()
        members = list()
        if "allOf" in schema:
            return self.handle_all_of(class_name, schema, parents)

        if "properties" in schema:
            required_props = schema.get('required', list())
            for name, data in schema["properties"].items():

                # handle default type references
                if "$ref" in data:
                    typename = self.class_name_from_ref(data["$ref"])
                    if typename in self.known_types:
                        data = self.known_types[typename]

                enums = None
                isdate = False
                required = name in required_props
                nullable = "nullable" in data and data["nullable"]

                # handle nullable references that are constructed with anyOf
                if "anyOf" in data:
                    data = self.handle_any_of(data, name, class_name)

                description = None
                if "description" in data:
                    description = data["description"]

                if "$ref" in data:
                    typename, default_value = self.handle_ref(data, required)
                    nullable = not required

                elif "type" not in data:
                    raise Warning(f"Cannot parse property without type for '{name}' in '{class_name}'")

                elif data["type"] == "array":
                    typename, default_value = self.handle_array(data, name, class_name, nullable)
                    imports.add("using System.Collections.Generic;\n")

                elif data["type"] == "object":
                    if "properties" in data:
                        print(name, data)
                        raise Warning(
                            f"Cannot parse property trees: '{name}' child of '{class_name}' should be declared in own schema directly under 'components'")
                    if "additionalProperties" in data:
                        typename, default_value = self.handle_additional_properties(data, nullable)
                        imports.add("using System.Collections.Generic;\n")
                    else:
                        raise Warning(
                            f"Cannot nested object without additionalProperties: '{name}' child of '{class_name}'")

                else:
                    typename, default_value = self.handle_default_type(data, nullable)
                    enums = self.handle_enums(name, data)
                    if enums != None:
                        imports.add("using System.Collections.Immutable;\n")
                    isdate = self.is_date(data)

                members.append(
                    MemberData(name, typename, isdate, nullable, default_value, name in required_props, description,
                               enums))
        description = None
        if "description" in schema:
            description = schema["description"]

        return ModelData(class_name, self.class_name(class_name), parents, members, imports, description)

    def handle_any_of(self, data: dict, name: str, class_name: str):
        anyof = data["anyOf"]
        if len(anyof) != 1:
            raise Warning(f"anyOf with multiple children not supported for '{name}' in '{class_name}'")
        anyof = anyof[0]
        if "$ref" not in anyof:
            raise Warning(f"anyOf child other than $ref not supported for '{name}' in '{class_name}'")
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

    def handle_array(self, data: dict, name: str, class_name: str, nullable: bool) -> Tuple[str, str]:
        items = data["items"]
        if "$ref" in items:
            typename = self.class_name_from_ref(items["$ref"])
        elif items["type"] not in ["string", "number", "integer", "boolean"]:
            raise Warning(
                f"Cannot parse array trees: '{name}' child of '{class_name}' should have it's array item declared in own schema directly under 'components'")
        else:
            typename = parse_type(items, nullable)
        default_value = f"new List<{typename}>()"
        typename = f"ICollection<{typename}>"

        return typename, default_value

    def handle_additional_properties(self, data: dict, nullable: bool) -> Tuple[str, str]:
        props = data['additionalProperties']
        if "$ref" in props:
            typename = self.class_name_from_ref(props["$ref"])
        else:
            typename = parse_type(props, nullable)
        typename = f"Dictionary<string, {typename}>"
        default_value = f"new {typename}()"
        return typename, default_value

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

    @staticmethod
    def is_date(schema: str):
        if "format" not in schema or "type" not in schema:
            return False
        return schema['type'] == "string" and schema['format'] == "date"

    def class_name_from_ref(self, param: str):
        name = param.split('/')[-1]
        return self.class_name(name)

    def class_name(self, name):
        return self.prefix + to_camelcase(name) + self.suffix

    def handle_all_of(self, class_name: str, schema: dict, parents: set):
        to_generate = None
        for element in schema["allOf"]:
            if "$ref" in element:
                parents.add(self.class_name_from_ref(element["$ref"]))
            if "type" in element or "properties" in element:
                if to_generate is not None:
                    raise Warning(
                        "allOf is implemented as inheritance; cannot have to children of allOf with direct implementation")
                to_generate = element
        if to_generate is None:
            logging.warning("Creating class without content, no child of allOf is type object")
            to_generate = dict()
        return self.parse_objects(class_name, to_generate, parents)

    def handle_enums(self, name: str, data: dict):
        if "enum" not in data:
            return None
        enum = data["enum"]
        if len(enum) == 0:
            return None
        typename, _ = self.handle_default_type(data, False)
        if typename not in ["string", "int", "long", "double"]:
            return None

        names = list()
        lines = list()
        for value in enum:
            varname = to_camelcase(name) + to_camelcase(value) + "Value"
            varname = re.sub(r"[^A-Za-z0-9]+", '_', varname)
            names.append(varname)
            if typename == "string":
                value = f'"{value}"'
            line = f"public const {typename} {varname} = {value};"
            lines.append(line)

        listname = "AllowedValuesFor" + to_camelcase(name)
        values = ", ".join(names)
        line = f"public static readonly ImmutableArray<{typename}> {listname} = new ImmutableArray<{typename}>() {{ {values} }};"
        lines.append(line)
        return "\n\t\t".join(lines)
