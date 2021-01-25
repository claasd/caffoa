import os
from typing import List, Set, Union, Optional

from prance import BaseParser
from caffoa.converter import parse_type, to_camelcase, is_date, TEMPLATE_FOLDER


class MemberData:
    def __init__(self, name: str, type: str, is_date: bool, nullable : bool, default_value: Optional[str], is_required: bool, description : Optional[str]):
        self.name = name
        self.type = type
        self.is_date = is_date
        self.nullable = nullable
        self.default_value = default_value
        self.is_required = is_required
        self.description = description


class ModelData:
    def __init__(self, name: str, parents: list, properties: List[MemberData], imports: Set[str]):
        self.name = name
        self.parents = parents
        self.properties = properties
        self.imports = imports


def class_name_from_ref(ref: str) -> str:
    return to_camelcase(ref.split('/')[-1])


def parse_properties(properties: dict):
    for variable, variable_type in properties.items():
        if "$ref" in variable_type:
            type = class_name_from_ref(variable_type["$ref"])
        else:
            type = parse_type(variable_type)
        print(variable, type)


def parse_schema(schema: dict, class_name: str, parents=None):
    imports = set()
    if parents is None:
        parents = list()
    members = list()
    if "allOf" in schema:
        for element in schema["allOf"]:
            if "$ref" in element:
                parents.append(class_name_from_ref(element["$ref"]))
            if "type" in element or "properties" in element:
                return parse_schema(element, class_name, parents)

    elif "properties" in schema or schema["type"] == "object":
        required_props = schema.get('required', list())
        for name, data in schema["properties"].items():
            description = None
            if "description" in data:
                description = data["description"]
                print(description)
            isdate = False
            nullable = "nullable" in data and data["nullable"]
            default_value = None
            if "$ref" in data:
                typename = class_name_from_ref(data["$ref"])
                if not nullable:
                    default_value = f"new {typename}()"
                else:
                    default_value = "null"
            elif "type" not in data:
                raise Warning(f"Cannot parse property without type for '{name}' in '{class_name}'")
            elif data["type"] == "object":
                if "properties" in data:
                    raise Warning(f"Cannot parse property trees: '{name}' child of '{class_name}' should be declared in own schema directly under 'components'")
                if "additionalProperties" in data:
                    props = data['additionalProperties']
                    if "$ref" not in props:
                        raise Warning("Cannot parse additionalProperties without direct reference")
                    typename = class_name_from_ref(props["$ref"])
                    typename = f"Dictionary<string, {typename}>"
                    imports.add("using System.Collections.Generic;\n")
            else:
                typename = parse_type(data, nullable)
                isdate = is_date(data)
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



            members.append(MemberData(name, typename, isdate, nullable, default_value, name in required_props, description))
    return ModelData(to_camelcase(class_name), parents, members, imports)


def write_model(model: ModelData, output_path: str, namespace: str):
    with open(TEMPLATE_FOLDER + "/ModelTemplate.cs", "r", encoding="utf-8") as f:
        model_Template = f.read()
    with open(TEMPLATE_FOLDER + "/ModelPropertyTemplate.cs", "r", encoding="utf-8") as f:
        prop_Template = f.read()
    properties = list()
    imports = "".join(model.imports)
    if len(model.parents) > 0:
        parents = " : " + ", ".join(model.parents)
    else:
        parents = ""
    has_dates = False
    for property in model.properties:
        if property.is_date:
            extra = "[JsonConverter(typeof(CustomJsonDateConverter))]\n\t\t"
            has_dates = True
        else:
            extra = ""
        default_str=""
        if property.default_value != None:
            default_str = f" = {property.default_value}"
        json_property_extra = ""
        if property.is_required and property.nullable:
            json_property_extra = ", Required = Required.AllowNull"
        elif property.is_required:
            json_property_extra = ", Required = Required.Always"
        elif not property.nullable:
            json_property_extra = ", Required = Required.DisallowNull"

        description = ""
        if property.description != None:
            description = f"/// <summary>\n\t\t/// {property.description}\n\t\t/// </summary>\n\t\t"

        properties.append(
            prop_Template.format(TYPE=property.type, NAMELOWER=property.name, NAMEUPPER=to_camelcase(property.name),
                                 JSON_EXTRA=extra, DEFAULT=default_str, JSON_PROPERTY_EXTRA=json_property_extra,
                                 DESCRIPTION=description))
    file_name = os.path.abspath(output_path + f"/{model.name}.generated.cs")
    print(f"Writing class {model.name} -> {file_name}")
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(model_Template.format(NAMESPACE=namespace, NAME=model.name, PROPERTIES="\n\n".join(properties),
                                      IMPORTS=imports, PARENTS=parents))
    if has_dates:
        with open(TEMPLATE_FOLDER + "/DateSerializer.cs", "r", encoding="utf-8") as f:
            date_converter_template = f.read()

        file_name = os.path.abspath(output_path + f"/CustomJsonDateConverter.generated.cs")
        print(f"Writing CustomJsonDateConverter -> {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(date_converter_template.format(NAMESPACE=namespace))


def generate_schemas(input_file: str, output_path: str, namespace: str):
    parser = BaseParser(input_file, strict=False)
    models = list()
    for name, schema in parser.specification["components"]["schemas"].items():
        models.append(parse_schema(schema, name))
    os.makedirs(output_path, exist_ok=True)
    for model in models:
        write_model(model, output_path, namespace)
