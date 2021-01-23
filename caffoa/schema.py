import os
from typing import List, Set

from prance import BaseParser
from caffoa.converter import parse_type, to_camelcase, is_date, TEMPLATE_FOLDER


class MemberData:
    def __init__(self, name: str, type: str, is_date: bool):
        self.name = name
        self.type = type
        self.is_date = is_date


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
        isdate = False
        for name, data in schema["properties"].items():
            if "$ref" in data:
                type = class_name_from_ref(data["$ref"])
            elif "type" not in data:
                print(data)
                raise Warning("Cannot parse property without type")
            elif data["type"] == "object":
                if "properties" in data:
                    print(data)
                    raise Warning("Cannot parse property trees")
                if "additionalProperties" in data:
                    props = data['additionalProperties']
                    if "$ref" not in props:
                        raise Warning("Cannot parse additionalProperties without direct reference")
                    type = class_name_from_ref(props["$ref"])
                    type = f"Dictionary<string, {type}>"
                    imports.add("using System.Collections.Generic;\n")
            else:
                type = parse_type(data)
                isdate = is_date(data)
            members.append(MemberData(name, type, isdate))
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
        properties.append(
            prop_Template.format(TYPE=property.type, NAMELOWER=property.name, NAMEUPPER=to_camelcase(property.name),
                                 JSON_EXTRA=extra))
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
    for model in models:
        write_model(model, output_path, namespace)
