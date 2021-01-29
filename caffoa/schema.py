import os

from caffoa.converter import to_camelcase, TEMPLATE_FOLDER
from caffoa.schema_parser import SchemaParser, ModelData


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
        default_str = ""
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

        enums = ""
        if property.enums != None:
            enums= f"{property.enums}\n\n\t\t"

        properties.append(
            prop_Template.format(TYPE=property.type, NAMELOWER=property.name, NAMEUPPER=to_camelcase(property.name),
                                 JSON_EXTRA=extra, DEFAULT=default_str, JSON_PROPERTY_EXTRA=json_property_extra,
                                 DESCRIPTION=description, ENUMS=enums))
    file_name = os.path.abspath(output_path + f"/{model.name}.generated.cs")
    print(f"Writing class {model.name} -> {file_name}")
    description = ""
    if model.description != None:
        description = f"/// <summary>\n\t/// {model.description}\n\t/// </summary>\n\t"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(model_Template.format(NAMESPACE=namespace, NAME=model.name, PROPERTIES="\n\n".join(properties),
                                      IMPORTS=imports, PARENTS=parents, DESCRIPTION=description))
    if has_dates:
        with open(TEMPLATE_FOLDER + "/DateSerializer.cs", "r", encoding="utf-8") as f:
            date_converter_template = f.read()

        file_name = os.path.abspath(output_path + f"/CustomJsonDateConverter.generated.cs")
        print(f"Writing CustomJsonDateConverter -> {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(date_converter_template.format(NAMESPACE=namespace))


def generate_schemas(input_file: str, output_path: str, namespace: str):
    # parser = BaseParser(input_file, strict=False)
    #models = list()
    # for name, schema in parser.specification["components"]["schemas"].items():
    #    models.append(parse_schema(schema, name))
    parser = SchemaParser()
    models = parser.parse(input_file)
    os.makedirs(output_path, exist_ok=True)
    for model in models:
        write_model(model, output_path, namespace)
